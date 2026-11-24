from app.balances import count_pairwise_debts, net_balances, pairwise_debts


def make_expense(paid_by, amount, shares):
    return {"paid_by": paid_by, "amount": amount, "shares": shares}


def test_no_expenses_everyone_zero():
    assert net_balances([], member_ids=["a", "b"]) == {"a": 0, "b": 0}


def test_one_expense_split_equally():
    expense = make_expense("a", 900, {"a": 300, "b": 300, "c": 300})
    assert net_balances([expense]) == {"a": 600, "b": -300, "c": -300}


def test_balances_always_add_up_to_zero():
    expenses = [
        make_expense("a", 1000, {"a": 250, "b": 250, "c": 250, "d": 250}),
        make_expense("b", 333, {"a": 111, "b": 111, "c": 111}),
        make_expense("d", 50, {"a": 10, "d": 40}),
    ]
    assert sum(net_balances(expenses).values()) == 0


def test_person_with_no_expenses_is_listed_with_zero():
    expense = make_expense("a", 200, {"a": 100, "b": 100})
    balances = net_balances([expense], member_ids=["a", "b", "z"])
    assert balances["z"] == 0


def test_paying_for_yourself_only_changes_nothing():
    expense = make_expense("a", 500, {"a": 500})
    assert net_balances([expense]) == {"a": 0}


# ---------- count_pairwise_debts (the "before" number) ----------

def test_no_expenses_no_debts():
    assert count_pairwise_debts([]) == 0


def test_one_expense_creates_one_debt_per_other_person():
    expense = make_expense("a", 900, {"a": 300, "b": 300, "c": 300})
    assert count_pairwise_debts([expense]) == 2  # b owes a, c owes a


def test_opposite_debts_between_two_people_cancel_into_one():
    first = make_expense("a", 1000, {"a": 500, "b": 500})  # b owes a 500
    second = make_expense("b", 300, {"a": 150, "b": 150})  # a owes b 150
    assert count_pairwise_debts([first, second]) == 1


def test_exactly_equal_opposite_debts_cancel_to_nothing():
    first = make_expense("a", 1000, {"a": 500, "b": 500})
    second = make_expense("b", 1000, {"a": 500, "b": 500})
    assert count_pairwise_debts([first, second]) == 0


def test_everyone_paid_once_for_everyone_gives_a_full_mesh():
    people = ["a", "b", "c", "d"]
    expenses = []
    for position, payer in enumerate(people):
        amount = 400 + position * 100  # different amounts so nothing cancels
        shares = {}
        for person in people:
            shares[person] = amount // 4
        expenses.append(make_expense(payer, amount, shares))
    # Different amounts -> every pair has a leftover debt: 4 people -> 6 pairs.
    assert count_pairwise_debts(expenses) == 6


def test_pairwise_debts_say_who_owes_whom_and_how_much():
    first = make_expense("a", 1000, {"a": 500, "b": 500})  # b owes a 500
    second = make_expense("b", 300, {"a": 150, "b": 150})  # a owes b 150
    assert pairwise_debts([first, second]) == [{"from": "b", "to": "a", "amount": 350}]


def test_pairwise_debts_flip_direction_when_the_other_person_owes_more():
    first = make_expense("a", 200, {"a": 100, "b": 100})  # b owes a 100
    second = make_expense("b", 1000, {"a": 500, "b": 500})  # a owes b 500
    assert pairwise_debts([first, second]) == [{"from": "a", "to": "b", "amount": 400}]
