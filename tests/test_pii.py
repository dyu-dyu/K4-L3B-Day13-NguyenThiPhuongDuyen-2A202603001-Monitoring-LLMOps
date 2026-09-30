from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_cccd() -> None:
    fake_cccd = "012345678901"
    out = scrub_text(f"CCCD: {fake_cccd}")
    assert fake_cccd not in out
    assert "REDACTED_CCCD" in out


def test_scrub_credit_card_formats() -> None:
    fake_cards = (
        "4111 1111 1111 1111",
        "4111-1111-1111-1111",
        "4111111111111111",
    )

    for fake_card in fake_cards:
        out = scrub_text(f"Card: {fake_card}")
        assert fake_card not in out
        assert "REDACTED_CREDIT_CARD" in out


def test_scrub_vietnamese_passport_formats() -> None:
    fake_passports = ("P1234567", "AB1234567")

    for fake_passport in fake_passports:
        out = scrub_text(f"Passport: {fake_passport}")
        assert fake_passport not in out
        assert "REDACTED_PASSPORT_VN" in out


def test_scrub_vietnamese_address() -> None:
    fake_address = "Địa chỉ: 123 Đường Mẫu, Phường 1, Quận A"
    out = scrub_text(fake_address)
    assert fake_address not in out
    assert "REDACTED_ADDRESS_VN" in out


def test_scrub_bank_account() -> None:
    fake_account = "1234567890"
    out = scrub_text(f"STK: {fake_account}")
    assert fake_account not in out
    assert "REDACTED_BANK_ACCOUNT" in out


def test_scrub_vietnamese_tax_id() -> None:
    fake_tax_id = "1234567890-123"
    out = scrub_text(f"MST: {fake_tax_id}")
    assert fake_tax_id not in out
    assert "REDACTED_TAX_ID_VN" in out


def test_scrub_date_of_birth() -> None:
    fake_date_of_birth = "01/01/2000"
    out = scrub_text(f"Ngày sinh: {fake_date_of_birth}")
    assert fake_date_of_birth not in out
    assert "REDACTED_DATE_OF_BIRTH" in out


def test_scrub_ip_address() -> None:
    fake_ip_address = "192.0.2.10"
    out = scrub_text(f"IP: {fake_ip_address}")
    assert fake_ip_address not in out
    assert "REDACTED_IP_ADDRESS" in out
