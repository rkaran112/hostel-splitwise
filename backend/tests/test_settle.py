import random

import pytest

from app.settle import settle_up
from tests.helpers import apply_payments, optimal_payment_count


def payments_for(balances):
    return settle_up(balances)["payments"]


# ---------- the edge cases ----------

def test_everyone_even_means_no_payments():
    result = settle_up({"a": 0, "b": 0, "c": 0})
    assert result["payments"] == []
    assert result["steps"] == []


def test_nobody_in_the_group_is_fine():
    assert settle_up({})["payments"] == []


def test_two_people():
    assert payments_for({"a": 500, "b": -500}) == [{"from": "b", "to": "a", "amount": 500}]


def test_one_person_owes_everyone():
    # d owes 900, split across three people who are each owed something.
    balances = {"a": 100, "b": 300, "c": 500, "d": -900}
    payments = payments_for(balances)
    assert len(payments) == 3
    assert all(p["from"] == "d" for p in payments)
    assert apply_payments(balances, payments) == {"a": 0, "b": 0, "c": 0, "d": 0}


def test_one_person_is_owed_by_everyone():
    balances = {"a": 900, "b": -100, "c": -300, "d": -500}
    payments = payments_for(balances)
    assert len(payments) == 3
    assert all(p["to"] == "a" for p in payments)
    assert apply_payments(balances, payments) == {"a": 0, "b": 0, "c": 0, "d": 0}


def test_biggest_debtor_pays_biggest_creditor_first():
    balances = {
        "big_creditor": 700,
        "small_creditor": 100,
        "big_debtor": -600,
        "small_debtor": -200,
    }
    first = payments_for(balances)[0]
    assert first == {"from": "big_debtor", "to": "big_creditor", "amount": 600}


def test_rounding_case_from_a_split_bill():
    # Rs 100 split 3 ways, paid by `a`: shares 3334, 3333, 3333 -> balances 6666, -3333, -3333
    balances = {"a": 6666, "b": -3333, "c": -3333}
    payments = payments_for(balances)
    assert len(payments) == 2
    assert apply_payments(balances, payments) == {"a": 0, "b": 0, "c": 0}


def test_single_paisa_is_settled_exactly():
    balances = {"a": 1, "b": -1}
    assert payments_for(balances) == [{"from": "b", "to": "a", "amount": 1}]


def test_balances_that_do_not_add_to_zero_are_rejected():
    with pytest.raises(ValueError):
        settle_up({"a": 500, "b": -400})


def test_input_is_not_changed():
    balances = {"a": 500, "b": -500}
    settle_up(balances)
    assert balances == {"a": 500, "b": -500}


# ---------- the steps used by the "show me how" walkthrough ----------

def test_steps_match_payments_and_end_empty():
    balances = {"a": 800, "b": 600, "c": -600, "d": -400, "e": -400}
    result = settle_up(balances)
    assert len(result["steps"]) == len(result["payments"])
    last = result["steps"][-1]
    assert last["debtors_left"] == []
    assert last["creditors_left"] == []


def test_first_step_shows_who_is_left():
    result = settle_up({"a": 800, "b": -300, "c": -500})
    first = result["steps"][0]
    assert (first["from"], first["to"], first["amount"]) == ("c", "a", 500)
    assert first["debtors_left"] == [{"person": "b", "amount": 300}]
    assert first["creditors_left"] == [{"person": "a", "amount": 300}]


# ---------- properties that must hold for ANY group ----------

def random_balances(rng, people):
    """Random whole-paise balances that add up to exactly 0."""
    names = [f"p{i}" for i in range(people)]
    amounts = [rng.randint(-5000, 5000) for _ in range(people - 1)]
    amounts.append(-sum(amounts))
    return dict(zip(names, amounts))


def test_properties_on_many_random_groups():
    rng = random.Random(42)  # fixed seed -> the same groups every run
    for _ in range(300):
        balances = random_balances(rng, rng.randint(2, 12))
        payments = payments_for(balances)

        people_with_balance = sum(1 for b in balances.values() if b != 0)
        assert len(payments) <= max(people_with_balance - 1, 0)  # at most n - 1
        assert all(p["amount"] > 0 for p in payments)  # no zero payments
        assert all(p["from"] != p["to"] for p in payments)  # nobody pays themselves
        assert all(balances[p["from"]] < 0 for p in payments)  # only debtors pay
        assert all(balances[p["to"]] > 0 for p in payments)  # only creditors receive
        assert all(v == 0 for v in apply_payments(balances, payments).values())  # all settled


# ---------- greedy vs the true optimum ----------

def test_greedy_is_never_better_than_optimal_and_never_worse_than_n_minus_1():
    rng = random.Random(7)
    for _ in range(200):
        balances = random_balances(rng, rng.randint(2, 9))
        greedy = len(payments_for(balances))
        best = optimal_payment_count(balances)
        non_zero = sum(1 for b in balances.values() if b != 0)
        assert best <= greedy <= max(non_zero - 1, 0)


def test_optimal_helper_on_a_known_case():
    # {b, c} cancel out and {a, d, e} cancel out -> 5 people - 2 groups = 3 payments.
    balances = {"a": 8, "b": 6, "c": -6, "d": -4, "e": -4}
    assert optimal_payment_count(balances) == 3


def test_greedy_is_not_always_optimal():
    """The honest limitation, written down as a test.

    Optimal is 3 payments:  c->b 6,  d->a 4,  e->a 4.
    Greedy needs 4:         c->a 6,  d->b 4,  e->b 2,  e->a 2.
    Greedy wastes a payment because c paying a first splits e's debt in two.
    """
    balances = {"a": 8, "b": 6, "c": -6, "d": -4, "e": -4}
    assert optimal_payment_count(balances) == 3
    assert len(payments_for(balances)) == 4


def test_greedy_is_optimal_when_no_subgroup_cancels_out():
    # Only the whole group sums to zero, so n - 1 payments is the best anyone can do.
    balances = {"a": 7, "b": 5, "c": -3, "d": -9}
    assert optimal_payment_count(balances) == 3
    assert len(payments_for(balances)) == 3
