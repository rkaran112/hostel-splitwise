"""
The shapes of the JSON the API accepts. FastAPI checks every request against these
before our code runs, and answers 422 with a clear message if something is off.

Money in requests is typed as rupees TEXT ("250.50"), because that is what a person
types. We turn it into paise on the server (money.py), so there is one parser to trust.
Money in responses is always whole PAISE.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.upi import is_valid_upi_id

MAX_MEMBERS = 20

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]


def clean_upi_id(value):
    """Blank means 'no UPI ID'. Anything else must look like name@bank."""
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    if not is_valid_upi_id(value):
        raise ValueError("That does not look like a UPI ID (example: asha@okhdfcbank)")
    return value


class MemberIn(BaseModel):
    name: Name
    upi_id: str | None = None

    @field_validator("upi_id")
    @classmethod
    def check_upi_id(cls, value):
        return clean_upi_id(value)


class GroupIn(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
    members: list[MemberIn] = Field(min_length=2, max_length=MAX_MEMBERS)


class UpiIdIn(BaseModel):
    upi_id: str | None = None

    @field_validator("upi_id")
    @classmethod
    def check_upi_id(cls, value):
        return clean_upi_id(value)


class ExpenseIn(BaseModel):
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    paid_by: int  # member id
    amount: str  # rupees as typed, e.g. "250.50"
    split_type: Literal["equal", "exact"]
    participants: list[int] = []  # for "equal": member ids sharing the bill
    shares: dict[int, str] = {}  # for "exact": member id -> rupees text
