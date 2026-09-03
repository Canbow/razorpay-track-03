"""Generates the benchmark dataset of 60 diverse failed payment records."""
import json
import random
from pathlib import Path
from decimal import Decimal
from typing import List, Dict, Any


def generate_batch_60_records() -> List[Dict[str, Any]]:
    """
    Generate 60 diverse failed payment events partitioned into 4 distinct subsets:
    - Subset 1 (Records 1–25): Transient infrastructure/bank issues (ISSUER_DOWN, GATEWAY_TIMEOUT, NETWORK_ERROR)
    - Subset 2 (Records 26–45): Actionable soft failures (INSUFFICIENT_FUNDS, AUTH_FAILED, EXPIRED_MANDATE)
    - Subset 3 (Records 46–52): Rate-limited / exhausted retries (attempt_count = 2)
    - Subset 4 (Records 53–60): Hard terminal failures (ACCOUNT_CLOSED, FRAUD_BLOCK, INVALID_ACCOUNT)
    """
    # Deterministic seed for reproducible batch generation
    rng = random.Random(42)
    records: List[Dict[str, Any]] = []

    # Subset 1: Records 1–25 (Transient Infrastructure/Bank Issues)
    transient_errors = [
        ("GATEWAY_TIMEOUT", "Payment gateway timed out waiting for bank switch response"),
        ("ISSUER_DOWN", "Issuing bank core banking system currently unreachable"),
        ("NETWORK_ERROR", "TCP handshake failure between gateway and NPCI switch"),
    ]
    transient_rails = ["MANDATE", "CARD", "NETBANKING"]

    for i in range(1, 26):
        err_code, err_desc = rng.choice(transient_errors)
        rail = rng.choice(transient_rails)
        amount = Decimal(rng.randint(15, 100) * 100)  # 1500 to 10000 in steps of 100
        hour = rng.randint(0, 23)
        records.append({
            "invoice_id": f"INV-REC-{i:04d}",
            "customer_id": f"CUST-{1000 + i:04d}",
            "amount": str(amount),
            "payment_rail": rail,
            "error_code": err_code,
            "error_description": err_desc,
            "attempt_count": 0,
            "failed_at": f"2026-09-03T{hour:02d}:15:00.000Z",
            "is_locked": False,
        })

    # Subset 2: Records 26–45 (Actionable Soft Failures)
    actionable_errors = [
        ("INSUFFICIENT_FUNDS", "Customer account has insufficient funds for clearing"),
        ("AUTH_FAILED", "3D Secure 2.0 two-factor authentication failed or cancelled by user"),
        ("EXPIRED_MANDATE", "Recurring mandate validity expired or unapproved limit"),
    ]
    actionable_rails = ["CARD", "UPI", "NETBANKING"]

    for i in range(26, 46):
        err_code, err_desc = rng.choice(actionable_errors)
        rail = rng.choice(actionable_rails)
        amount = Decimal(rng.randint(5, 50) * 100)  # 500 to 5000 in steps of 100
        hour = rng.randint(8, 19)  # within typical business daytime
        records.append({
            "invoice_id": f"INV-REC-{i:04d}",
            "customer_id": f"CUST-{1000 + i:04d}",
            "amount": str(amount),
            "payment_rail": rail,
            "error_code": err_code,
            "error_description": err_desc,
            "attempt_count": 0,
            "failed_at": f"2026-09-03T{hour:02d}:30:00.000Z",
            "is_locked": False,
        })

    # Subset 3: Records 46–52 (Rate-limited / Exhausted Retries)
    exhausted_errors = [
        ("INSUFFICIENT_FUNDS", "Account balance depleted after multiple debit attempts"),
        ("GATEWAY_TIMEOUT", "Third consecutive bank timeout during retry window"),
        ("AUTH_FAILED", "Two successive OTP authentication timeouts"),
    ]
    for i in range(46, 53):
        err_code, err_desc = rng.choice(exhausted_errors)
        rail = rng.choice(["UPI", "CARD", "MANDATE"])
        amount = Decimal(rng.randint(10, 75) * 100)  # 1000 to 7500
        records.append({
            "invoice_id": f"INV-REC-{i:04d}",
            "customer_id": f"CUST-{1000 + i:04d}",
            "amount": str(amount),
            "payment_rail": rail,
            "error_code": err_code,
            "error_description": err_desc,
            "attempt_count": 2,  # MAX_RETRY_LIMIT reached
            "failed_at": f"2026-09-03T09:{i:02d}:00.000Z",
            "is_locked": False,
        })

    # Subset 4: Records 53–60 (Hard Terminal Failures)
    terminal_errors = [
        ("ACCOUNT_CLOSED", "Drawee account permanently closed or non-existent"),
        ("FRAUD_BLOCK", "Account flagged by card scheme / NPCI risk engine for suspicious activity"),
        ("INVALID_ACCOUNT", "Beneficiary account number or IFSC code invalid"),
    ]
    for i in range(53, 61):
        err_code, err_desc = rng.choice(terminal_errors)
        rail = rng.choice(["CARD", "NETBANKING", "MANDATE", "UPI"])
        amount = Decimal(rng.randint(12, 80) * 100)  # 1200 to 8000
        records.append({
            "invoice_id": f"INV-REC-{i:04d}",
            "customer_id": f"CUST-{1000 + i:04d}",
            "amount": str(amount),
            "payment_rail": rail,
            "error_code": err_code,
            "error_description": err_desc,
            "attempt_count": 0,
            "failed_at": f"2026-09-03T11:{i:02d}:00.000Z",
            "is_locked": False,
        })

    return records


def write_batch_dataset(output_path: Path) -> Path:
    """Generate and write the benchmark JSON dataset to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset = generate_batch_60_records()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)
    return output_path


def get_default_dataset_path() -> Path:
    """Get the standard dataset path."""
    return Path(__file__).parent / "failed_payments_batch_60.json"


if __name__ == "__main__":
    target = get_default_dataset_path()
    path = write_batch_dataset(target)
    print(f"Successfully generated 60 failed payment records at: {path}")
