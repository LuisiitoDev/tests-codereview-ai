from __future__ import annotations

from decimal import Decimal

import pytest

from payments_svc.amounts import (
    MAX_AMOUNT,
    AmountError,
    CurrencyError,
    calculate_fee,
    normalize_currency,
    parse_amount,
    round_money,
    total_with_fee,
    validate_amount,
)


# ---------------------------------------------------------------------------
# parse_amount
# ---------------------------------------------------------------------------

class TestParseAmount:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("10.50", Decimal("10.50")),
            ("  10.50  ", Decimal("10.50")),
            (10, Decimal("10")),
            (10.5, Decimal("10.5")),
            (Decimal("10.50"), Decimal("10.50")),
            ("0", Decimal("0")),
            ("-5.00", Decimal("-5.00")),
        ],
    )
    def test_parses_valid_values(self, raw, expected):
        assert parse_amount(raw) == expected

    def test_none_raises(self):
        with pytest.raises(AmountError):
            parse_amount(None)

    @pytest.mark.parametrize("raw", ["abc", "", "12.34.56", "1,000"])
    def test_non_numeric_string_raises(self, raw):
        with pytest.raises(AmountError):
            parse_amount(raw)

    @pytest.mark.parametrize("raw", ["NaN", "Infinity", "-Infinity"])
    def test_non_finite_raises(self, raw):
        with pytest.raises(AmountError):
            parse_amount(raw)


# ---------------------------------------------------------------------------
# normalize_currency
# ---------------------------------------------------------------------------

class TestNormalizeCurrency:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("usd", "USD"),
            ("USD", "USD"),
            ("  eur  ", "EUR"),
            ("cop", "COP"),
        ],
    )
    def test_normalizes_supported_currencies(self, raw, expected):
        assert normalize_currency(raw) == expected

    def test_none_raises(self):
        with pytest.raises(CurrencyError):
            normalize_currency(None)

    @pytest.mark.parametrize("raw", ["", "   "])
    def test_blank_raises(self, raw):
        with pytest.raises(CurrencyError):
            normalize_currency(raw)

    def test_unsupported_currency_raises(self):
        with pytest.raises(CurrencyError):
            normalize_currency("GBP")


# ---------------------------------------------------------------------------
# validate_amount
# ---------------------------------------------------------------------------

class TestValidateAmount:
    @pytest.mark.parametrize(
        "amount",
        [Decimal("0"), Decimal("0.01"), Decimal("500.00"), MAX_AMOUNT],
    )
    def test_valid_amounts_do_not_raise(self, amount):
        validate_amount(amount)

    def test_negative_raises(self):
        with pytest.raises(AmountError):
            validate_amount(Decimal("-0.01"))

    def test_above_max_raises(self):
        with pytest.raises(AmountError):
            validate_amount(MAX_AMOUNT + Decimal("0.01"))


# ---------------------------------------------------------------------------
# round_money
# ---------------------------------------------------------------------------

class TestRoundMoney:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (Decimal("1.005"), Decimal("1.00")),  # round-half-even: down
            (Decimal("1.015"), Decimal("1.02")),  # round-half-even: up
            (Decimal("1.025"), Decimal("1.02")),  # round-half-even: down
            (Decimal("1.234"), Decimal("1.23")),
            (Decimal("1.236"), Decimal("1.24")),
            (Decimal("10"), Decimal("10.00")),
        ],
    )
    def test_rounds_half_even(self, value, expected):
        assert round_money(value) == expected


# ---------------------------------------------------------------------------
# calculate_fee
# ---------------------------------------------------------------------------

class TestCalculateFee:
    def test_zero_amount_returns_zero_fee(self):
        assert calculate_fee(Decimal("0"), "USD") == Decimal("0.00")

    def test_percentage_fee_used_when_above_minimum(self):
        # 100.00 * 2.9% = 2.90, above the 0.30 minimum.
        assert calculate_fee(Decimal("100.00"), "USD") == Decimal("2.90")

    def test_minimum_fee_used_when_percentage_below_minimum(self):
        # 1.00 * 2.9% = 0.029, below the 0.30 minimum.
        assert calculate_fee(Decimal("1.00"), "USD") == Decimal("0.30")

    def test_currency_is_case_insensitive(self):
        assert calculate_fee(Decimal("100.00"), "usd") == Decimal("2.90")

    def test_unsupported_currency_raises(self):
        with pytest.raises(CurrencyError):
            calculate_fee(Decimal("100.00"), "GBP")

    def test_negative_amount_raises(self):
        with pytest.raises(AmountError):
            calculate_fee(Decimal("-1.00"), "USD")

    def test_amount_above_max_raises(self):
        with pytest.raises(AmountError):
            calculate_fee(MAX_AMOUNT + Decimal("0.01"), "USD")

    def test_eur_minimum_fee(self):
        assert calculate_fee(Decimal("1.00"), "EUR") == Decimal("0.25")

    def test_cop_percentage_fee(self):
        # 100000.00 * 1.9% = 1900.00, above the 900.00 minimum.
        assert calculate_fee(Decimal("100000.00"), "COP") == Decimal("1900.00")


# ---------------------------------------------------------------------------
# total_with_fee
# ---------------------------------------------------------------------------

class TestTotalWithFee:
    def test_adds_fee_to_amount(self):
        assert total_with_fee(Decimal("100.00"), "USD") == Decimal("102.90")

    def test_zero_amount_returns_zero_total(self):
        assert total_with_fee(Decimal("0"), "USD") == Decimal("0.00")

    def test_negative_amount_raises(self):
        with pytest.raises(AmountError):
            total_with_fee(Decimal("-1.00"), "USD")

    def test_unsupported_currency_raises(self):
        with pytest.raises(CurrencyError):
            total_with_fee(Decimal("100.00"), "GBP")
