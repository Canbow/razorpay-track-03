"""Synthetic 60-record dataset generator for 3-way reconciliation."""
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path so relative imports work if run directly
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.rules import CONTRACTED_MDR_RATE, GST_RATE, TWO_PLACES, quantize_currency


def get_dataset_path() -> Path:
    """Return the canonical dataset JSON file path."""
    return CURRENT_DIR / "dataset_batch_60.json"


def generate_dataset(output_path: Path = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate deterministic 60-record dataset:
    - Records 1-40: Clean 3-way matches (MDR 2% + GST 18%)
    - Records 41-48: Fee Discrepancy (Gateway charged MDR 3% instead of contracted 2%)
    - Records 49-54: Unsettled in Bank (Settled by Gateway with UTR, missing in Bank dump)
    - Records 55-60: Missing Gateway Record (Marked PAID in OMS, missing in Gateway dump)
    """
    target_file = output_path or get_dataset_path()
    target_file.parent.mkdir(parents=True, exist_ok=True)

    internal_orders: List[Dict[str, Any]] = []
    razorpay_settlements: List[Dict[str, Any]] = []
    bank_statement_entries: List[Dict[str, Any]] = []

    # Deterministic base amounts for realistic diversity
    base_amounts = [
        Decimal("1499.00"), Decimal("2999.00"), Decimal("4500.00"), Decimal("7850.50"),
        Decimal("12000.00"), Decimal("15499.00"), Decimal("22000.00"), Decimal("35000.00"),
        Decimal("48999.00"), Decimal("50000.00"), Decimal("1850.00"), Decimal("3200.00"),
        Decimal("6750.00"), Decimal("9999.00"), Decimal("13500.00"), Decimal("17800.00"),
        Decimal("24500.00"), Decimal("31000.00"), Decimal("42500.00"), Decimal("49900.00")
    ]

    # --- 1. Records 1 to 40: Clean Matches ---
    for i in range(1, 41):
        order_num = 1000 + i
        order_id = f"ORD_{order_num}"
        payment_id = f"pay_clean_{order_num}"
        utr = f"UTR20260901CLEAN{order_num:04d}"
        bank_ref = f"BNK_REF_{order_num:04d}"
        customer_id = f"CUST_{(order_num % 15) + 1:03d}"

        amount = base_amounts[(i - 1) % len(base_amounts)] + Decimal(f"{i * 10}.00")
        tax_amount = quantize_currency(amount * Decimal("0.18"))  # 18% internal tax

        # Contracted 2% MDR
        fee = quantize_currency(amount * CONTRACTED_MDR_RATE)
        tax_on_fee = quantize_currency(fee * GST_RATE)
        net_amount = quantize_currency(amount - (fee + tax_on_fee))

        # OMS Order
        internal_orders.append({
            "order_id": order_id,
            "amount": str(amount),
            "tax_amount": str(tax_amount),
            "customer_id": customer_id,
            "status": "PAID",
            "created_at": f"2026-09-01T{10 + (i % 8):02d}:{(i * 3) % 60:02d}:00Z",
        })

        # Gateway Settlement
        razorpay_settlements.append({
            "payment_id": payment_id,
            "order_id": order_id,
            "gross_amount": str(amount),
            "fee": str(fee),
            "tax_on_fee": str(tax_on_fee),
            "net_amount": str(net_amount),
            "utr": utr,
            "settled_at": f"2026-09-01T{11 + (i % 8):02d}:{(i * 3) % 60:02d}:00Z",
        })

        # Bank Entry
        bank_statement_entries.append({
            "bank_ref": bank_ref,
            "utr": utr,
            "credit_amount": str(net_amount),
            "value_date": "2026-09-01",
            "description": f"ACH CR RAZORPAY SETTLEMENT {utr}",
        })

    # --- 2. Records 41 to 48: Fee Discrepancy (Gateway charged 3% MDR instead of 2%) ---
    OVERCHARGED_MDR_RATE = Decimal("0.03")  # 3.0% MDR
    for i in range(41, 49):
        order_num = 1000 + i
        order_id = f"ORD_{order_num}"
        payment_id = f"pay_overcharge_{order_num}"
        utr = f"UTR20260901FEEERR{order_num:04d}"
        bank_ref = f"BNK_REF_{order_num:04d}"
        customer_id = f"CUST_{(order_num % 15) + 1:03d}"

        amount = base_amounts[(i - 1) % len(base_amounts)] + Decimal(f"{i * 25}.00")
        tax_amount = quantize_currency(amount * Decimal("0.18"))

        # Overcharged 3% MDR
        fee = quantize_currency(amount * OVERCHARGED_MDR_RATE)
        tax_on_fee = quantize_currency(fee * GST_RATE)
        net_amount = quantize_currency(amount - (fee + tax_on_fee))

        # OMS Order
        internal_orders.append({
            "order_id": order_id,
            "amount": str(amount),
            "tax_amount": str(tax_amount),
            "customer_id": customer_id,
            "status": "PAID",
            "created_at": f"2026-09-01T{12 + (i % 4):02d}:{(i * 5) % 60:02d}:00Z",
        })

        # Gateway Settlement (Deducted 3% instead of contracted 2%)
        razorpay_settlements.append({
            "payment_id": payment_id,
            "order_id": order_id,
            "gross_amount": str(amount),
            "fee": str(fee),
            "tax_on_fee": str(tax_on_fee),
            "net_amount": str(net_amount),
            "utr": utr,
            "settled_at": f"2026-09-01T{13 + (i % 4):02d}:{(i * 5) % 60:02d}:00Z",
        })

        # Bank Entry (Merchant received what gateway disbursed, but fee was overcharged)
        bank_statement_entries.append({
            "bank_ref": bank_ref,
            "utr": utr,
            "credit_amount": str(net_amount),
            "value_date": "2026-09-01",
            "description": f"ACH CR RAZORPAY SETTLEMENT {utr}",
        })

    # --- 3. Records 49 to 54: Unsettled in Bank (Settled in Razorpay with UTR, missing in Bank) ---
    for i in range(49, 55):
        order_num = 1000 + i
        order_id = f"ORD_{order_num}"
        payment_id = f"pay_unsettled_{order_num}"
        utr = f"UTR20260901UNSTLD{order_num:04d}"
        customer_id = f"CUST_{(order_num % 15) + 1:03d}"

        amount = base_amounts[(i - 1) % len(base_amounts)] + Decimal(f"{i * 15}.00")
        tax_amount = quantize_currency(amount * Decimal("0.18"))

        fee = quantize_currency(amount * CONTRACTED_MDR_RATE)
        tax_on_fee = quantize_currency(fee * GST_RATE)
        net_amount = quantize_currency(amount - (fee + tax_on_fee))

        # OMS Order
        internal_orders.append({
            "order_id": order_id,
            "amount": str(amount),
            "tax_amount": str(tax_amount),
            "customer_id": customer_id,
            "status": "PAID",
            "created_at": f"2026-09-01T14:{(i * 7) % 60:02d}:00Z",
        })

        # Gateway Settlement exists and shows settled with UTR
        razorpay_settlements.append({
            "payment_id": payment_id,
            "order_id": order_id,
            "gross_amount": str(amount),
            "fee": str(fee),
            "tax_on_fee": str(tax_on_fee),
            "net_amount": str(net_amount),
            "utr": utr,
            "settled_at": f"2026-09-01T15:{(i * 7) % 60:02d}:00Z",
        })

        # MISSING in Bank Statement! (No entry added for this UTR)

    # --- 4. Records 55 to 60: Missing Gateway Record (Marked PAID in OMS, missing in Razorpay dump) ---
    for i in range(55, 61):
        order_num = 1000 + i
        order_id = f"ORD_{order_num}"
        customer_id = f"CUST_{(order_num % 15) + 1:03d}"

        amount = base_amounts[(i - 1) % len(base_amounts)] + Decimal(f"{i * 30}.00")
        tax_amount = quantize_currency(amount * Decimal("0.18"))

        # OMS Order marked PAID
        internal_orders.append({
            "order_id": order_id,
            "amount": str(amount),
            "tax_amount": str(tax_amount),
            "customer_id": customer_id,
            "status": "PAID",
            "created_at": f"2026-09-01T16:{(i * 9) % 60:02d}:00Z",
        })

        # MISSING in Razorpay Settlements dump!
        # MISSING in Bank Statement dump!

    dataset = {
        "metadata": {
            "total_internal_orders": len(internal_orders),
            "total_settlements": len(razorpay_settlements),
            "total_bank_entries": len(bank_statement_entries),
            "clean_matches_expected": 40,
            "fee_discrepancy_expected": 8,
            "unsettled_bank_expected": 6,
            "missing_gateway_expected": 6,
        },
        "internal_orders": internal_orders,
        "razorpay_settlements": razorpay_settlements,
        "bank_statement_entries": bank_statement_entries,
    }

    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"Generated 60-record dataset at: {target_file}")
    print(f"  - Internal Orders: {len(internal_orders)}")
    print(f"  - Razorpay Settlements: {len(razorpay_settlements)}")
    print(f"  - Bank Statement Entries: {len(bank_statement_entries)}")

    return dataset


if __name__ == "__main__":
    generate_dataset()
