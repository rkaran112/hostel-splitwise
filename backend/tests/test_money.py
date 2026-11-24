import pytest

from app.money import (
    check_exact_split,
    paise_to_rupees_str,
    rupees_to_paise,
    split_equally,
)


# ---------- rupees_to_paise ----------

def test_whole_rupees():
    assert rupees_to_paise("12") == 1200


def test_one_decimal_digit_means_tens_of_paise():
    assert rupees_to_paise("12.5") == 1250


def test_two_decimal_digits():
    assert rupees_to_paise("12.50") == 1250
    assert rupees_to_paise("0.01") == 1


def test_surrounding_spaces_are_ignored():
    assert rupees_to_paise("  7.25 ") == 725


def test_float_trap_amounts_stay_exact():
    # With floats, 0.1 + 0.2 != 0.3. With paise it is exact.
    assert rupees_to_paise("0.1") + rupees_to_paise("0.2") == rupees_to_paise("0.3")


@pytest.mark.parametrize("bad", ["", "abc", "12.345", "-5", "1,000", "12.", ".5", "1e3"])
def test_bad_amounts_are_rejected(bad):
    with pytest.raises(ValueError):
        rupees_to_paise(bad)


# ---------- paise_to_rupees_str ----------

def test_paise_to_string():
    assert paise_to_rupees_str(1250) == "12.50"
    assert paise_to_rupees_str(5) == "0.05"
    assert paise_to_rupees_str(0) == "0.00"
    assert paise_to_rupees_str(100000) == "1000.00"


def test_negative_paise_to_string():
    assert paise_to_rupees_str(-1250) == "-12.50"


def test_round_trip():
    for text in ["0.01", "12.50", "999.99", "100.00"]:
        assert paise_to_rupees_str(rupees_to_paise(text)) == text


# ---------- split_equally ----------

def test_even_split():
    assert split_equally(9000, ["a", "b", "c"]) == {"a": 3000, "b": 3000, "c": 3000}


def test_rupees_100_among_3_rounding():
    shares = split_equally(rupees_to_paise("100"), ["a", "b", "c"])
    assert shares == {"a": 3334, "b": 3333, "c": 3333}
    assert sum(shares.values()) == 10000


def test_one_paisa_among_3_people():
    shares = split_equally(1, ["a", "b", "c"])
    assert shares == {"a": 1, "b": 0, "c": 0}


def test_split_always_adds_up_to_total():
    for total in [1, 2, 7, 99, 10000, 123457]:
        for people in range(1, 9):
            ids = list(range(people))
            assert sum(split_equally(total, ids).values()) == total


def test_split_with_one_person():
    assert split_equally(500, ["solo"]) == {"solo": 500}


def test_split_rejects_zero_amount_or_nobody():
    with pytest.raises(ValueError):
        split_equally(0, ["a"])
    with pytest.raises(ValueError):
        split_equally(100, [])


# ---------- check_exact_split ----------

def test_exact_split_that_adds_up_is_fine():
    check_exact_split(1000, {"a": 400, "b": 600})


def test_exact_split_that_does_not_add_up_is_rejected():
    with pytest.raises(ValueError):
        check_exact_split(1000, {"a": 400, "b": 500})


def test_exact_split_rejects_negative_share():
    with pytest.raises(ValueError):
        check_exact_split(1000, {"a": 1500, "b": -500})


def test_exact_split_rejects_empty():
    with pytest.raises(ValueError):
        check_exact_split(1000, {})
