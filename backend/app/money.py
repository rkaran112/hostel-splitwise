"""
Money helpers.

THE BIG IDEA: we never store rupees as decimals. We store PAISE as whole numbers.
    Rs 12.50  ->  1250 paise
Whole numbers never have rounding errors. Floats do:  0.1 + 0.2 = 0.30000000000000004

So every amount inside this app is an `int` of paise. Rupees only appear at the
edges: when a person types an amount, and when we show one on screen.
"""


def rupees_to_paise(text):
    """Turn what a person typed ("12", "12.5", "12.50") into paise (1200, 1250, 1250).

    We cut the text at the "." and read the two halves as whole numbers.
    We never use float(), so there is no rounding error to worry about.
    """
    text = text.strip()
    rupees_part, dot, paise_part = text.partition(".")

    if not rupees_part.isdigit():
        raise ValueError("Amount must look like 12 or 12.50")
    if dot and not paise_part.isdigit():
        raise ValueError("Amount must look like 12 or 12.50")
    if len(paise_part) > 2:
        raise ValueError("Amount can have at most 2 digits after the dot")

    paise_part = paise_part.ljust(2, "0")  # "5" -> "50", "" -> "00"
    return int(rupees_part) * 100 + int(paise_part)


def paise_to_rupees_str(paise):
    """Turn paise into a display string: 1250 -> "12.50". Uses divmod, not float."""
    sign = "-" if paise < 0 else ""
    rupees, leftover_paise = divmod(abs(paise), 100)
    return f"{sign}{rupees}.{leftover_paise:02d}"


def split_equally(total_paise, member_ids):
    """Split a bill equally. Returns {member_id: share_in_paise}.

    Rs 100 among 3 people is 10000 paise. 10000 / 3 does not divide evenly:
        each person gets 3333 paise, and 1 paise is left over.
    The leftover paise are handed out one each to the first people in the list.
    So the shares are 3334, 3333, 3333, and they ALWAYS add up to the total.
    """
    if total_paise <= 0:
        raise ValueError("Amount must be more than zero")
    if len(member_ids) == 0:
        raise ValueError("Need at least one person to split between")

    base_share, leftover = divmod(total_paise, len(member_ids))

    shares = {}
    for position, member_id in enumerate(member_ids):
        extra = 1 if position < leftover else 0
        shares[member_id] = base_share + extra
    return shares


def check_exact_split(total_paise, shares):
    """For 'exact amounts' splits: make sure the shares add up to the total.

    `shares` is {member_id: paise}. Raises ValueError if anything is off.
    """
    if total_paise <= 0:
        raise ValueError("Amount must be more than zero")
    if len(shares) == 0:
        raise ValueError("Need at least one person to split between")
    for paise in shares.values():
        if paise < 0:
            raise ValueError("A share cannot be negative")

    shares_total = sum(shares.values())
    if shares_total != total_paise:
        raise ValueError(
            f"Shares add up to {shares_total} paise but the bill is {total_paise} paise"
        )
