"""
Balances: who is owed money and who owes money.

An expense is a plain dict:
    {"paid_by": "asha", "amount": 4000_00, "shares": {"asha": 1000_00, "ben": 1000_00, ...}}
    - paid_by : the person who handed over the cash
    - amount  : the whole bill, in paise
    - shares  : how much of the bill each person is responsible for, in paise
                (these add up to `amount`)

NET BALANCE of a person = (what they paid out) - (what they should have paid).
    positive -> the group owes them money   (a "creditor")
    negative -> they owe the group money    (a "debtor")
Across the whole group the balances always add up to exactly 0.
"""


def net_balances(expenses, member_ids=()):
    """Return {person: net_balance_in_paise}.

    `member_ids` lets us list people who have no expenses yet, so they show up with 0.
    """
    balances = {}
    for member_id in member_ids:
        balances[member_id] = 0

    for expense in expenses:
        payer = expense["paid_by"]
        balances[payer] = balances.get(payer, 0) + expense["amount"]

        for person, share in expense["shares"].items():
            balances[person] = balances.get(person, 0) - share

    return balances


def _ordered_pair(person_a, person_b):
    """Always return the same ordering for a pair, so (A, B) and (B, A) match."""
    if person_a < person_b:
        return person_a, person_b
    return person_b, person_a


def count_pairwise_debts(expenses):
    """The 'BEFORE' number: how many separate debts exist without simplifying?

    For every expense, each person who has a share owes the payer that share.
    If Ben owes Asha 700 from one trip and Asha owes Ben 300 from another, those
    cancel into ONE debt of 400. We net every pair of people this way, then count
    the pairs that still owe something.
    """
    # For each pair (first, second): positive means `second` owes `first`.
    pair_totals = {}

    for expense in expenses:
        payer = expense["paid_by"]
        for person, share in expense["shares"].items():
            if person == payer:
                continue  # you do not owe yourself

            first, second = _ordered_pair(payer, person)
            if payer == first:
                pair_totals[(first, second)] = pair_totals.get((first, second), 0) + share
            else:
                pair_totals[(first, second)] = pair_totals.get((first, second), 0) - share

    debts = 0
    for total in pair_totals.values():
        if total != 0:
            debts += 1
    return debts
