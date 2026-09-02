"""Deterministic financial math invariants and rule verification engine."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple
from .models import InternalOrder, RazorpaySettlement, BankStatementEntry

# Contracted standard rates
CONTRACTED_MDR_RATE = Decimal("0.02")  # 2.0%
GST_RATE = Decimal("0.18")             # 18.0% GST on MDR

TWO_PLACES = Decimal("0.01")


def quantize_currency(value: Decimal) -> Decimal:
    """Quantize decimal currency value to 2 decimal places using standard ROUND_HALF_UP."""
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_expected_fee(gross_amount: Decimal) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Calculate expected MDR fee, GST on MDR, and total expected fee.
    Returns:
        (expected_mdr, expected_gst, total_expected_fee)
    """
    gross = Decimal(str(gross_amount))
    expected_mdr = quantize_currency(gross * CONTRACTED_MDR_RATE)
    expected_gst = quantize_currency(expected_mdr * GST_RATE)
    total_expected_fee = expected_mdr + expected_gst
    return expected_mdr, expected_gst, total_expected_fee


def check_fee_overcharge(settlement: RazorpaySettlement) -> Tuple[bool, Decimal, Decimal, Decimal]:
    """
    Compare actual gateway fees deducted against contracted rates.
    Returns:
        (is_overcharged: bool, delta: Decimal, expected_total: Decimal, actual_total: Decimal)
    """
    _, _, expected_total = calculate_expected_fee(settlement.gross_amount)
    actual_total = quantize_currency(settlement.fee + settlement.tax_on_fee)
    delta = actual_total - expected_total

    # Overcharged if actual fee exceeds expected fee by more than 0.00
    is_overcharged = delta > Decimal("0.00")
    return is_overcharged, delta, expected_total, actual_total


def verify_accounting_equation(
    order: InternalOrder,
    settlement: RazorpaySettlement,
    bank_entry: BankStatementEntry,
) -> Tuple[bool, str]:
    """
    Strictly verifies fundamental double-entry & gateway accounting invariants:
    1. Order Amount == Gateway Gross Amount
    2. Gateway Gross - (MDR Fee + GST) == Gateway Net Settlement
    3. Gateway Net Settlement == Bank Statement Credit Amount
    """
    # 1. Order amount vs Gateway gross
    if quantize_currency(order.amount) != quantize_currency(settlement.gross_amount):
        return (
            False,
            f"Gross Mismatch: Order amount ({order.amount}) != Gateway gross ({settlement.gross_amount})",
        )

    # 2. Gateway internal math
    expected_net = quantize_currency(settlement.gross_amount - (settlement.fee + settlement.tax_on_fee))
    if quantize_currency(settlement.net_amount) != expected_net:
        return (
            False,
            f"Gateway Math Violation: Net amount ({settlement.net_amount}) != Gross - (Fee + GST) ({expected_net})",
        )

    # 3. Gateway net vs Bank credit
    if quantize_currency(settlement.net_amount) != quantize_currency(bank_entry.credit_amount):
        return (
            False,
            f"Bank Settlement Mismatch: Gateway net ({settlement.net_amount}) != Bank credit ({bank_entry.credit_amount})",
        )

    return True, "All accounting equations balanced."
