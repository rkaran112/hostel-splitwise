import pytest

from app.upi import build_upi_link, is_valid_upi_id


def test_basic_link():
    link = build_upi_link("asha@okhdfcbank", "Asha", 25000)
    assert link == "upi://pay?pa=asha@okhdfcbank&pn=Asha&am=250.00&cu=INR"


def test_amount_always_has_two_decimals():
    assert "am=0.05&" in build_upi_link("a1@ybl", "A", 5)
    assert "am=12.50&" in build_upi_link("a1@ybl", "A", 1250)


def test_name_with_space_is_encoded():
    link = build_upi_link("asha@ybl", "Asha Kumar", 100)
    assert "pn=Asha%20Kumar&" in link


def test_name_with_ampersand_cannot_break_the_link():
    link = build_upi_link("asha@ybl", "Tom & Jerry", 100)
    assert "pn=Tom%20%26%20Jerry&" in link
    # Exactly four fields: pa, pn, am, cu.
    assert link.count("&") == 3


def test_phone_number_upi_id():
    assert build_upi_link("9876543210@ybl", "Ben", 100).startswith("upi://pay?pa=9876543210@ybl")


@pytest.mark.parametrize("good", ["asha@okhdfcbank", "a.b-c_d@ybl", "9876543210@paytm"])
def test_valid_upi_ids(good):
    assert is_valid_upi_id(good)


@pytest.mark.parametrize("bad", ["", "asha", "@ybl", "asha@", "a b@ybl", "asha@@ybl", "asha@yb1"])
def test_invalid_upi_ids(bad):
    assert not is_valid_upi_id(bad)


def test_build_rejects_bad_id_and_bad_amount():
    with pytest.raises(ValueError):
        build_upi_link("not-an-id", "Asha", 100)
    with pytest.raises(ValueError):
        build_upi_link("asha@ybl", "Asha", 0)
    with pytest.raises(ValueError):
        build_upi_link("asha@ybl", "Asha", -5)
