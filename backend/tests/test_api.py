"""
API tests: they call the real routes with a real (temporary) database.
"""


def make_group(client, names=("Asha", "Ben", "Chirag"), upi_ids=None):
    members = []
    for position, name in enumerate(names):
        member = {"name": name}
        if upi_ids and upi_ids.get(name):
            member["upi_id"] = upi_ids[name]
        members.append(member)
    response = client.post("/api/groups", json={"name": "Trip", "members": members})
    assert response.status_code == 200, response.text
    return response.json()


def ids_by_name(group):
    return {member["name"]: member["id"] for member in group["members"]}


def add_equal_expense(client, group, payer, amount, people, description="Bill"):
    ids = ids_by_name(group)
    body = {
        "description": description,
        "paid_by": ids[payer],
        "amount": amount,
        "split_type": "equal",
        "participants": [ids[name] for name in people],
    }
    return client.post(f"/api/groups/{group['id']}/expenses", json=body)


# ---------- groups ----------

def test_create_group_and_read_it_back(client):
    group = make_group(client)
    assert len(group["id"]) >= 8
    assert [m["name"] for m in group["members"]] == ["Asha", "Ben", "Chirag"]

    again = client.get(f"/api/groups/{group['id']}").json()
    assert again["name"] == "Trip"
    assert again["expenses"] == []
    assert [b["balance"] for b in again["balances"]] == [0, 0, 0]


def test_unknown_group_is_404(client):
    assert client.get("/api/groups/doesnotexist").status_code == 404


def test_group_needs_two_people(client):
    response = client.post("/api/groups", json={"name": "Solo", "members": [{"name": "A"}]})
    assert response.status_code == 422


def test_duplicate_names_are_rejected(client):
    response = client.post(
        "/api/groups", json={"name": "T", "members": [{"name": "Asha"}, {"name": "asha"}]}
    )
    assert response.status_code == 400


def test_bad_upi_id_is_rejected(client):
    response = client.post(
        "/api/groups",
        json={"name": "T", "members": [{"name": "A", "upi_id": "nope"}, {"name": "B"}]},
    )
    assert response.status_code == 422


def test_add_member_and_set_upi_id(client):
    group = make_group(client)
    added = client.post(f"/api/groups/{group['id']}/members", json={"name": "Dev"}).json()
    assert added["name"] == "Dev"

    patched = client.patch(
        f"/api/groups/{group['id']}/members/{added['id']}", json={"upi_id": "dev@ybl"}
    ).json()
    assert patched["upi_id"] == "dev@ybl"


# ---------- expenses ----------

def test_equal_expense_updates_balances(client):
    group = make_group(client)
    response = add_equal_expense(client, group, "Asha", "900", ["Asha", "Ben", "Chirag"])
    assert response.status_code == 200

    balances = client.get(f"/api/groups/{group['id']}").json()["balances"]
    by_name = {b["name"]: b["balance"] for b in balances}
    assert by_name == {"Asha": 60000, "Ben": -30000, "Chirag": -30000}


def test_rounding_shares_add_up_exactly(client):
    group = make_group(client)
    add_equal_expense(client, group, "Asha", "100", ["Asha", "Ben", "Chirag"])
    expense = client.get(f"/api/groups/{group['id']}").json()["expenses"][0]
    shares = [s["share"] for s in expense["shares"]]
    assert sorted(shares) == [3333, 3333, 3334]
    assert sum(shares) == expense["amount"] == 10000


def test_exact_split(client):
    group = make_group(client)
    ids = ids_by_name(group)
    body = {
        "description": "Dinner",
        "paid_by": ids["Ben"],
        "amount": "500",
        "split_type": "exact",
        "shares": {str(ids["Asha"]): "100", str(ids["Ben"]): "150.50", str(ids["Chirag"]): "249.50"},
    }
    response = client.post(f"/api/groups/{group['id']}/expenses", json=body)
    assert response.status_code == 200
    assert sum(s["share"] for s in response.json()["shares"]) == 50000


def test_exact_split_that_does_not_add_up_is_400(client):
    group = make_group(client)
    ids = ids_by_name(group)
    body = {
        "description": "Dinner",
        "paid_by": ids["Ben"],
        "amount": "500",
        "split_type": "exact",
        "shares": {str(ids["Asha"]): "100", str(ids["Ben"]): "100"},
    }
    response = client.post(f"/api/groups/{group['id']}/expenses", json=body)
    assert response.status_code == 400
    assert "add up" in response.json()["detail"]


def test_bad_amounts_are_400(client):
    group = make_group(client)
    for bad in ["", "abc", "12.345", "-5", "0", "99999999999"]:
        response = add_equal_expense(client, group, "Asha", bad, ["Asha", "Ben"])
        assert response.status_code == 400, bad


def test_member_of_another_group_is_rejected(client):
    group = make_group(client)
    other = make_group(client, names=("X", "Y"))
    body = {
        "description": "Sneaky",
        "paid_by": other["members"][0]["id"],
        "amount": "10",
        "split_type": "equal",
        "participants": [m["id"] for m in group["members"]],
    }
    assert client.post(f"/api/groups/{group['id']}/expenses", json=body).status_code == 400


def test_delete_expense_is_a_soft_delete(client):
    group = make_group(client)
    expense = add_equal_expense(client, group, "Asha", "300", ["Asha", "Ben"]).json()

    assert client.delete(f"/api/groups/{group['id']}/expenses/{expense['id']}").status_code == 200
    after = client.get(f"/api/groups/{group['id']}").json()
    assert after["expenses"] == []
    assert [b["balance"] for b in after["balances"]] == [0, 0, 0]

    # The row is still counted as "created" by the usage counter.
    assert client.get("/api/stats").json()["expenses"] == 1
    # Deleting twice is a 404.
    assert client.delete(f"/api/groups/{group['id']}/expenses/{expense['id']}").status_code == 404


# ---------- settle up ----------

def test_settle_nothing_to_do(client):
    group = make_group(client)
    result = client.get(f"/api/groups/{group['id']}/settle").json()
    assert result["payments"] == []
    assert result["before_debts"] == 0
    assert result["after_payments"] == 0


def test_settle_gives_payments_and_upi_links(client):
    group = make_group(client, upi_ids={"Asha": "asha@okhdfcbank"})
    add_equal_expense(client, group, "Asha", "900", ["Asha", "Ben", "Chirag"])

    result = client.get(f"/api/groups/{group['id']}/settle").json()
    assert result["before_debts"] == 2
    assert result["after_payments"] == 2
    for payment in result["payments"]:
        assert payment["to_name"] == "Asha"
        assert payment["amount"] == 30000
        assert payment["upi_link"] == "upi://pay?pa=asha@okhdfcbank&pn=Asha&am=300.00&cu=INR"


def test_settle_without_upi_id_has_no_link(client):
    group = make_group(client)
    add_equal_expense(client, group, "Asha", "900", ["Asha", "Ben", "Chirag"])
    payments = client.get(f"/api/groups/{group['id']}/settle").json()["payments"]
    assert all(p["upi_link"] is None for p in payments)


# ---------- demo group and usage counter ----------

def test_demo_group_matches_the_readme_example(client):
    demo = client.post("/api/groups/demo").json()
    assert demo["is_demo"] is True
    assert len(demo["expenses"]) == 5

    result = client.get(f"/api/groups/{demo['id']}/settle").json()
    assert result["before_debts"] == 9
    assert result["after_payments"] == 4
    assert all(p["upi_link"].startswith("upi://pay?") for p in result["payments"])


def test_usage_counter_ignores_demo_groups(client):
    client.post("/api/groups/demo")
    assert client.get("/api/stats").json() == {"groups": 0, "expenses": 0, "demo_groups": 1}

    group = make_group(client)
    add_equal_expense(client, group, "Asha", "90", ["Asha", "Ben"])
    add_equal_expense(client, group, "Ben", "60", ["Asha", "Ben"])
    assert client.get("/api/stats").json() == {"groups": 1, "expenses": 2, "demo_groups": 1}
