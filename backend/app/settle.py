"""
Settle up: the fewest-payments plan, found with a greedy algorithm and two heaps.

THE IDEA IN PLAIN WORDS
    Everyone has a net balance (see balances.py). Some people are owed money
    (creditors), some owe money (debtors). Repeat until nobody owes anything:
        1. Take the person who owes the MOST.
        2. Take the person who is owed the MOST.
        3. The debtor pays the creditor as much as possible: min(debt, credit).
        4. At least one of the two is now fully settled and leaves.
           The other (if not settled) goes back with their smaller amount.

    Each payment settles at least one person, so for n people there are at most
    n - 1 payments. Python's heapq gives "who owes the most?" in O(log n),
    so the whole thing takes O(n log n).

    heapq is a MIN-heap (smallest first). We want the BIGGEST first, so we
    store amounts as negative numbers: -500 comes out before -300.
"""

import heapq


def _build_heap(amounts):
    """Turn {person: amount} into a heap of (-amount, person), biggest amount on top."""
    heap = []
    for person, amount in amounts.items():
        heap.append((-amount, person))
    heapq.heapify(heap)
    return heap


def _snapshot(heap):
    """A readable copy of a heap, biggest first: [{"person": ..., "amount": ...}]."""
    items = sorted(heap)  # sorted on (-amount, person) = biggest amount first
    return [{"person": person, "amount": -neg_amount} for neg_amount, person in items]


def _check_balances(balances):
    """Balances of a real group add up to 0. If not, the data is wrong."""
    total = sum(balances.values())
    if total != 0:
        raise ValueError(f"Balances must add up to 0, but they add up to {total}")


def settle_up(balances):
    """Work out who pays whom.

    `balances` is {person: net_balance_in_paise}.
    Returns {"payments": [...], "steps": [...]}
      payments: [{"from": debtor, "to": creditor, "amount": paise}, ...]
      steps:    one entry per payment, with who is still unsettled afterwards
                (the UI uses this for the "show me how" walkthrough)
    """
    _check_balances(balances)

    creditors = {}  # person -> how much they are owed
    debtors = {}  # person -> how much they owe (as a positive number)
    for person, balance in balances.items():
        if balance > 0:
            creditors[person] = balance
        elif balance < 0:
            debtors[person] = -balance

    credit_heap = _build_heap(creditors)
    debt_heap = _build_heap(debtors)

    payments = []
    steps = []

    while debt_heap and credit_heap:
        neg_debt, debtor = heapq.heappop(debt_heap)
        neg_credit, creditor = heapq.heappop(credit_heap)
        debt = -neg_debt
        credit = -neg_credit

        amount = min(debt, credit)
        payments.append({"from": debtor, "to": creditor, "amount": amount})

        # Whoever still has something left goes back into their heap.
        if debt > amount:
            heapq.heappush(debt_heap, (-(debt - amount), debtor))
        if credit > amount:
            heapq.heappush(credit_heap, (-(credit - amount), creditor))

        steps.append(
            {
                "from": debtor,
                "to": creditor,
                "amount": amount,
                "debtors_left": _snapshot(debt_heap),
                "creditors_left": _snapshot(credit_heap),
            }
        )

    return {"payments": payments, "steps": steps}
