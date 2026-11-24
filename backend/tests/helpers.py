"""Small helpers shared by the tests. Not part of the app."""


def apply_payments(balances, payments):
    """Pretend every payment happened and return the new balances.

    The debtor's balance goes UP (they paid off debt), the creditor's goes DOWN
    (they were repaid). If the plan is right, everyone ends at exactly 0.
    """
    result = dict(balances)
    for payment in payments:
        result[payment["from"]] += payment["amount"]
        result[payment["to"]] -= payment["amount"]
    return result


def optimal_payment_count(balances):
    """The TRUE minimum number of payments, found by brute force (slow, tiny inputs only).

    Idea: split the people into as many groups as possible where each group's
    balances add up to 0. A group of k people can settle among themselves in
    k - 1 payments. So:   minimum payments = (people) - (number of zero-sum groups).

    dp[mask] = the most zero-sum groups we can make from the people in `mask`.
    We add people one at a time; whenever the whole mask sums to 0, a group closes.
    """
    amounts = [b for b in balances.values() if b != 0]
    count = len(amounts)
    if count == 0:
        return 0

    mask_sum = [0] * (1 << count)
    best_groups = [0] * (1 << count)

    for mask in range(1, 1 << count):
        for person in range(count):
            if mask & (1 << person):
                without_person = mask ^ (1 << person)
                mask_sum[mask] = mask_sum[without_person] + amounts[person]
                best_groups[mask] = max(best_groups[mask], best_groups[without_person])
        if mask_sum[mask] == 0:
            best_groups[mask] += 1

    return count - best_groups[(1 << count) - 1]
