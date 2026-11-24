"""
UPI payment links.

A UPI link looks like this:
    upi://pay?pa=asha@okhdfcbank&pn=Asha%20K&am=250.00&cu=INR
        pa = payee address (their UPI ID)     pn = payee name
        am = amount in RUPEES                 cu = currency

When a phone opens this link, it offers GPay / PhonePe / Paytm with the amount
already filled in. THIS APP NEVER MOVES MONEY. It only builds the link text.
"""

import re
from urllib.parse import quote

from app.money import paise_to_rupees_str

# A UPI ID is  name@bank  -  e.g. "asha.k@okhdfcbank" or "9876543210@ybl".
UPI_ID_PATTERN = re.compile(r"^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$")


def is_valid_upi_id(upi_id):
    """True if the text looks like a UPI ID."""
    return UPI_ID_PATTERN.match(upi_id) is not None


def build_upi_link(upi_id, name, amount_paise):
    """Build the upi://pay link for one payment."""
    if not is_valid_upi_id(upi_id):
        raise ValueError("That does not look like a UPI ID")
    if amount_paise <= 0:
        raise ValueError("Amount must be more than zero")

    # quote() makes the name safe for a URL: "Asha & Co" -> "Asha%20%26%20Co".
    # Without this, an "&" in a name would break the link into extra fields.
    safe_name = quote(name, safe="")
    safe_upi_id = quote(upi_id, safe="@")  # keep the @ readable
    rupees = paise_to_rupees_str(amount_paise)  # the link wants rupees, e.g. 250.00

    return f"upi://pay?pa={safe_upi_id}&pn={safe_name}&am={rupees}&cu=INR"
