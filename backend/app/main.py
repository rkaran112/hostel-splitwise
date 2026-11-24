"""
The web API. Each route does four things: find the group, check the input,
call a function from service.py, return the answer. Keep the logic out of here.

Run it:   uvicorn app.main:app --reload      (docs at http://localhost:8000/docs)
"""

import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import service
from app.db import Base, engine, get_db
from app.models import Expense, Group, Member
from app.schemas import MAX_MEMBERS, ExpenseIn, GroupIn, MemberIn, UpiIdIn


@asynccontextmanager
async def lifespan(app):
    # Create the tables if they do not exist yet. (No migration tool: kept simple on purpose.)
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Hostel Splitwise", lifespan=lifespan)

# CORS: the browser only lets the website call this API if the API says the website is allowed.
# Live: ALLOWED_ORIGINS is set to the website's address. Laptop: not set, so any localhost port works.
allowed_origins = os.environ.get("ALLOWED_ORIGINS")
if allowed_origins is None:
    cors_settings = {"allow_origin_regex": r"http://localhost:\d+"}
else:
    cors_settings = {"allow_origins": [origin.strip() for origin in allowed_origins.split(",")]}

app.add_middleware(CORSMiddleware, allow_methods=["*"], allow_headers=["*"], **cors_settings)


def get_group_or_404(db, group_id):
    group = db.get(Group, group_id)
    if group is None:
        raise HTTPException(404, "Group not found. Check the link.")
    return group


def bad_request(error):
    return HTTPException(400, str(error))


def check_unique_names(names):
    seen = set()
    for name in names:
        key = name.lower()
        if key in seen:
            raise HTTPException(400, f"Two people are called {name}. Use different names.")
        seen.add(key)


# ---------- health check ----------

@app.get("/api/health")
def health():
    """Render calls this to know the server is up. It does not touch the database."""
    return {"status": "ok"}


# ---------- groups ----------

@app.post("/api/groups")
def create_group(body: GroupIn, db=Depends(get_db)):
    check_unique_names([member.name for member in body.members])
    group = service.create_group(db, body.name, body.members)
    return service.group_to_dict(group, [])


@app.post("/api/groups/demo")
def create_demo_group(db=Depends(get_db)):
    group = service.create_demo_group(db)
    return service.group_to_dict(group, service.active_expenses(db, group.id))


@app.get("/api/groups/{group_id}")
def get_group(group_id: str, db=Depends(get_db)):
    group = get_group_or_404(db, group_id)
    return service.group_to_dict(group, service.active_expenses(db, group.id))


# ---------- members ----------

@app.post("/api/groups/{group_id}/members")
def add_member(group_id: str, body: MemberIn, db=Depends(get_db)):
    group = get_group_or_404(db, group_id)
    if len(group.members) >= MAX_MEMBERS:
        raise HTTPException(400, f"A group can have at most {MAX_MEMBERS} people")
    check_unique_names([member.name for member in group.members] + [body.name])

    member = Member(group_id=group.id, name=body.name, upi_id=body.upi_id)
    db.add(member)
    db.commit()
    return service.member_to_dict(member)


@app.patch("/api/groups/{group_id}/members/{member_id}")
def set_upi_id(group_id: str, member_id: int, body: UpiIdIn, db=Depends(get_db)):
    member = db.get(Member, member_id)
    if member is None or member.group_id != group_id:
        raise HTTPException(404, "Person not found in this group")
    member.upi_id = body.upi_id
    db.commit()
    return service.member_to_dict(member)


# ---------- expenses ----------

@app.post("/api/groups/{group_id}/expenses")
def add_expense(group_id: str, body: ExpenseIn, db=Depends(get_db)):
    group = get_group_or_404(db, group_id)
    if len(service.active_expenses(db, group.id)) >= service.MAX_EXPENSES_PER_GROUP:
        raise HTTPException(400, "This group has reached its limit of expenses")

    member_ids = {member.id for member in group.members}
    try:
        amount, shares = service.work_out_shares(body, member_ids)
    except ValueError as error:
        raise bad_request(error)

    expense = service.save_expense(
        db, group.id, body.description, body.paid_by, amount, body.split_type, shares
    )
    return service.expense_to_dict(expense)


@app.delete("/api/groups/{group_id}/expenses/{expense_id}")
def delete_expense(group_id: str, expense_id: int, db=Depends(get_db)):
    expense = db.get(Expense, expense_id)
    if expense is None or expense.group_id != group_id or expense.deleted_at is not None:
        raise HTTPException(404, "Expense not found")
    expense.deleted_at = datetime.now(UTC)  # soft delete: the row stays, it just stops counting
    db.commit()
    return {"deleted": expense_id}


# ---------- settle up and stats ----------

@app.get("/api/groups/{group_id}/settle")
def settle(group_id: str, db=Depends(get_db)):
    group = get_group_or_404(db, group_id)
    return service.settle_to_dict(group, service.active_expenses(db, group.id))


@app.get("/api/stats")
def stats(db=Depends(get_db)):
    return service.usage_stats(db)
