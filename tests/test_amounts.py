"""Tests de contrato para src/payments_svc/amounts.py.

Cubre unicamente los modos de falla de FAILURE.MODES.md cuyo
"Estado del contrato" es Confirmado: FM-EQUIV-01 (EQ-01) y
FM-FRONT-03 (FRO-03). No se prueban modos pendientes de decision.
"""

from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from payments_svc.amounts import (
    AmountError,
    calculate_fee,
    parse_amount,
    total_with_fee,
    validate_amount,
)


class ParseAmountRejectsFloatContractTests(unittest.TestCase):
    """FM-EQUIV-01 / EQ-01: parse_amount debe rechazar cualquier `raw` de tipo float."""

    def test_parse_amount_rejects_plain_float(self):
        # FM-EQUIV-01
        # Arrange
        raw = 19.99

        # Act / Assert
        with self.assertRaises(AmountError):
            parse_amount(raw)

    def test_parse_amount_rejects_float_with_exact_integer_value(self):
        # FM-EQUIV-01
        # Arrange
        raw = 100.0

        # Act / Assert
        with self.assertRaises(AmountError):
            parse_amount(raw)

    def test_parse_amount_rejects_float_zero(self):
        # FM-EQUIV-01
        # Arrange
        raw = 0.0

        # Act / Assert
        with self.assertRaises(AmountError):
            parse_amount(raw)

    def test_parse_amount_rejects_float_nan(self):
        # FM-EQUIV-01
        # Arrange
        raw = float("nan")

        # Act / Assert
        with self.assertRaises(AmountError):
            parse_amount(raw)

    def test_parse_amount_rejects_float_infinity(self):
        # FM-EQUIV-01
        # Arrange
        raw = float("inf")

        # Act / Assert
        with self.assertRaises(AmountError):
            parse_amount(raw)

    def test_parse_amount_rejects_float_negative_infinity(self):
        # FM-EQUIV-01
        # Arrange
        raw = float("-inf")

        # Act / Assert
        with self.assertRaises(AmountError):
            parse_amount(raw)

    def test_parse_amount_still_accepts_non_float_numeric_types(self):
        # FM-EQUIV-01 (guarda de no-sobre-alcance: solo float se rechaza)
        # Arrange
        raw_str = "19.99"
        raw_int = 20
        raw_decimal = Decimal("19.99")

        # Act
        parsed_str = parse_amount(raw_str)
        parsed_int = parse_amount(raw_int)
        parsed_decimal = parse_amount(raw_decimal)

        # Assert
        self.assertEqual(parsed_str, Decimal("19.99"))
        self.assertEqual(parsed_int, Decimal("20"))
        self.assertEqual(parsed_decimal, Decimal("19.99"))


class ValidateAmountRejectsZeroContractTests(unittest.TestCase):
    """FM-FRONT-03 / FRO-03: validate_amount debe rechazar amount == 0."""

    def test_validate_amount_rejects_zero(self):
        # FM-FRONT-03
        # Arrange
        amount = Decimal("0")

        # Act / Assert
        with self.assertRaises(AmountError):
            validate_amount(amount)

    def test_validate_amount_rejects_zero_with_two_decimals(self):
        # FM-FRONT-03
        # Arrange
        amount = Decimal("0.00")

        # Act / Assert
        with self.assertRaises(AmountError):
            validate_amount(amount)

    def test_validate_amount_rejects_negative_zero(self):
        # FM-FRONT-03
        # Arrange
        amount = Decimal("-0.00")

        # Act / Assert
        with self.assertRaises(AmountError):
            validate_amount(amount)

    def test_validate_amount_still_accepts_smallest_positive_amount(self):
        # FM-FRONT-03 (guarda de no-sobre-alcance: el rango pasa a (0, MAX], no (algo > 0, MAX])
        # Arrange
        amount = Decimal("0.01")

        # Act / Assert (no debe lanzar AmountError; una excepcion aqui falla el test)
        validate_amount(amount)


class ZeroAmountCascadeThroughValidateAmountContractTests(unittest.TestCase):
    """FM-FRONT-03 / FRO-03: calculate_fee y total_with_fee llaman validate_amount
    antes que su propia logica, por lo que heredan el rechazo de amount == 0.
    No decide NEG-01 (exencion de fee); solo verifica la propagacion del contrato
    ya confirmado de validate_amount.
    """

    def test_calculate_fee_rejects_zero_amount(self):
        # FM-FRONT-03 (cascada via validate_amount)
        # Arrange
        amount = Decimal("0")
        currency = "USD"

        # Act / Assert
        with self.assertRaises(AmountError):
            calculate_fee(amount, currency)

    def test_total_with_fee_rejects_zero_amount(self):
        # FM-FRONT-03 (cascada via validate_amount)
        # Arrange
        amount = Decimal("0")
        currency = "USD"

        # Act / Assert
        with self.assertRaises(AmountError):
            total_with_fee(amount, currency)


if __name__ == "__main__":
    unittest.main()
