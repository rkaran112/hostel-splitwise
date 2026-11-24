"""
The glue between the database and the pure algorithm files.

main.py (the web routes) calls these functions. These functions read rows, turn them
into the plain dicts that balances.py and settle.py understand, and shape the answers.
"""

import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.balances import net_balances, pairwise_debts
from app.models import Expense, ExpenseShare, Group, Member
from app.money import check_exact_split, rupees_to_paise, split_equally
from app.schemas import MemberIn
from app.settle import settle_up
from app.upi import build_upi_link

MAX_EXPENSES_PER_GROUP = 500
MAX_AMOUNT_PAISE = 1_000_000_000  # Rs 1 crore. Keeps numbers inside a normal database integer.


# ---------- turning a request into shares ----------

def work_out_shares(body, member_ids):
    """Check an expense request and return (amount_in_paise, {member_id: share_in_paise}).

    Raises ValueError with a message a person can read if something is wrong.
    """
    amount = rupees_to_paise(body.amount)
    if amount > MAX_AMOUNT_PAISE:
        raise ValueError("That amount is too large")
    if body.paid_by not in member_ids:
        raise ValueError("The person who paid is not in this group")

    if body.split_type == "equal":
        return amount, equal_shares(amount, body.participants, member_ids)
    return amount, exact_shares(amount, body.shares, member_ids)


def equal_shares(amount, participants, member_ids):
    people = []
    for member_id in participants:
        if member_id not in member_ids:
            raise ValueError("Someone in the split is not in this group")
        if member_id not in people:  # ignore duplicates, keep the order
            people.append(member_id)
    return split_equally(amount, people)


def exact_shares(amount, typed_shares, member_ids):
    shares = {}
    for member_id, text in typed_shares.items():
        if member_id not in member_ids:
            raise ValueError("Someone in the split is not in this group")
        shares[member_id] = rupees_to_paise(text)
    check_exact_split(amount, shares)
    return shares


# ---------- reading from the database ----------

def active_expenses(db, group_id):
    """All expenses of a group that have not been deleted, oldest first."""
    query = (
        select(Expense)
        .where(Expense.group_id == group_id, Expense.deleted_at.is_(None))
        .options(selectinload(Expense.shares))
        .order_by(Expense.id)
    )
    return list(db.scalars(query))


def expenses_for_math(expenses):
    """Turn database rows into the plain dicts that balances.py expects."""
    result = []
    for expense in expenses:
        shares = {}
        for share in expense.shares:
            shares[share.member_id] = share.share_paise
        result.append({"paid_by": expense.paid_by, "amount": expense.amount_paise, "shares": shares})
    return result


def group_to_dict(group, expenses):
    """Everything the group page needs in one answer."""
    math_expenses = expenses_for_math(expenses)
    member_ids = [member.id for member in group.members]
    balances = net_balances(math_expenses, member_ids)

    return {
        "id": group.id,
        "name": group.name,
        "is_demo": group.is_demo,
        "members": [member_to_dict(member) for member in group.members],
        "expenses": [expense_to_dict(expense) for expense in reversed(expenses)],  # newest first
        "balances": [
            {"member_id": member.id, "name": member.name, "balance": balances[member.id]}
            for member in group.members
        ],
    }


def member_to_dict(member):
    return {"id": member.id, "name": member.name, "upi_id": member.upi_id}


def expense_to_dict(expense):
    return {
        "id": expense.id,
        "description": expense.description,
        "paid_by": expense.paid_by,
        "amount": expense.amount_paise,
        "split_type": expense.split_type,
        "created_at": expense.created_at.isoformat(),
        "shares": [{"member_id": s.member_id, "share": s.share_paise} for s in expense.shares],
    }


# ---------- settle up ----------

def settle_to_dict(group, expenses):
    """Run the algorithm and shape the answer: payments with UPI links, plus the steps."""
    math_expenses = expenses_for_math(expenses)
    member_ids = [member.id for member in group.members]
    balances = net_balances(math_expenses, member_ids)
    result = settle_up(balances)

    members = {member.id: member for member in group.members}
    payments = [payment_to_dict(payment, members) for payment in result["payments"]]
    steps = [step_to_dict(step, members) for step in result["steps"]]

    debts = [debt_to_dict(debt, members) for debt in pairwise_debts(math_expenses)]

    return {
        "before_debts": len(debts),
        "after_payments": len(payments),
        "debts": debts,
        "payments": payments,
        "steps": steps,
    }


def debt_to_dict(debt, members):
    return {
        "from_name": members[debt["from"]].name,
        "to_name": members[debt["to"]].name,
        "amount": debt["amount"],
    }


def payment_to_dict(payment, members):
    payer = members[payment["from"]]
    receiver = members[payment["to"]]

    upi_link = None
    if receiver.upi_id:
        upi_link = build_upi_link(receiver.upi_id, receiver.name, payment["amount"])

    return {
        "from_id": payer.id,
        "from_name": payer.name,
        "to_id": receiver.id,
        "to_name": receiver.name,
        "to_upi_id": receiver.upi_id,
        "amount": payment["amount"],
        "upi_link": upi_link,
    }


def step_to_dict(step, members):
    return {
        "from_name": members[step["from"]].name,
        "to_name": members[step["to"]].name,
        "amount": step["amount"],
        "debtors_left": named_people(step["debtors_left"], members),
        "creditors_left": named_people(step["creditors_left"], members),
    }


def named_people(people, members):
    return [{"name": members[p["person"]].name, "amount": p["amount"]} for p in people]


# ---------- writing to the database ----------

def create_group(db, name, member_inputs, is_demo=False):
    group = Group(id=secrets.token_urlsafe(8), name=name, is_demo=is_demo)
    for member_input in member_inputs:
        group.members.append(Member(name=member_input.name, upi_id=member_input.upi_id))
    db.add(group)
    db.commit()
    return group


def save_expense(db, group_id, description, paid_by, amount, split_type, shares):
    expense = Expense(
        group_id=group_id,
        description=description,
        paid_by=paid_by,
        amount_paise=amount,
        split_type=split_type,
    )
    for member_id, share in shares.items():
        expense.shares.append(ExpenseShare(member_id=member_id, share_paise=share))
    db.add(expense)
    db.commit()
    return expense


# ---------- the demo group ----------

# (description, who paid, rupees, who shares it; None means everybody)
DEMO_EXPENSES = [
    ("Hotel", "Asha", 6000, None),
    ("Food", "Ben", 5000, ["Ben", "Chirag", "Dev", "Esha"]),
    ("Cab", "Chirag", 1500, ["Asha", "Chirag", "Dev"]),
    ("Tickets", "Dev", 1000, None),
    ("Snacks", "Esha", 500, ["Ben", "Esha"]),
]

# These UPI IDs are made up (the bank part "upi" does not exist), so no real person is paid.
DEMO_PEOPLE = ["Asha", "Ben", "Chirag", "Dev", "Esha"]


def create_demo_group(db):
    people = [MemberIn(name=name, upi_id=name.lower() + ".demo@upi") for name in DEMO_PEOPLE]
    group = create_group(db, "Goa trip (demo)", people, is_demo=True)
    ids = {member.name: member.id for member in group.members}

    for description, payer, rupees, who in DEMO_EXPENSES:
        names = who if who is not None else DEMO_PEOPLE
        amount = rupees * 100
        shares = split_equally(amount, [ids[name] for name in names])
        save_expense(db, group.id, description, ids[payer], amount, "equal", shares)
    return group


# ---------- usage counter ----------

def usage_stats(db):
    """Real usage only: demo groups are counted separately so they do not inflate the numbers."""
    groups = db.scalar(select(func.count()).select_from(Group).where(Group.is_demo.is_(False)))
    expenses = db.scalar(
        select(func.count())
        .select_from(Expense)
        .join(Group, Group.id == Expense.group_id)
        .where(Group.is_demo.is_(False))
    )
    demo_groups = db.scalar(select(func.count()).select_from(Group).where(Group.is_demo.is_(True)))
    return {"groups": groups, "expenses": expenses, "demo_groups": demo_groups}
