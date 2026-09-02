"""Real CSV Ingestion Adapter for 3-Way Reconciliation."""
import csv
import io
import os
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Union

# Ensure root is on path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.models import InternalOrder, RazorpaySettlement, BankStatementEntry
from core.rules import quantize_currency
from data.generate_batch import get_dataset_path


def clean_currency_str(val: Any) -> Decimal:
    """Sanitize currency string (e.g. '₹ 10,000.50', 'INR 1000', ' 1500.00 ') into Decimal."""
    if val is None:
        return Decimal("0.00")
    if isinstance(val, (int, float, Decimal)):
        return quantize_currency(Decimal(str(val)))

    s = str(val).strip()
    if not s:
        return Decimal("0.00")

    # Strip currency signs, 'INR', '₹', '$', commas, quotes
    cleaned = re.sub(r"[^\d.-]", "", s)
    if not cleaned or cleaned in ("-", ".", "-."):
        return Decimal("0.00")
    try:
        return quantize_currency(Decimal(cleaned))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Unable to parse '{val}' into a valid financial Decimal amount.")


def normalize_str(s: str) -> str:
    """Normalize string by removing non-alphanumerics and converting to lowercase."""
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def find_column_val(row: Dict[str, str], aliases: List[str], default: Any = "") -> str:
    """
    Find a value in a CSV row matching any of the candidate header aliases.
    Checks exact matches first, then prefix/containment matching.
    """
    normalized_row = {normalize_str(k): v for k, v in row.items() if k is not None}

    # 1. Exact normalized match
    for alias in aliases:
        norm_alias = normalize_str(alias)
        if norm_alias in normalized_row:
            val = normalized_row[norm_alias]
            if val is not None and str(val).strip():
                return str(val).strip()

    # 2. Prefix / Containment match (e.g., 'orderamountinr' contains 'orderamount')
    for alias in aliases:
        norm_alias = normalize_str(alias)
        if len(norm_alias) < 4:  # Avoid ambiguous short matches like 'id'
            continue
        for k, v in normalized_row.items():
            if norm_alias in k:
                if v is not None and str(v).strip():
                    return str(v).strip()

    return default


def _get_reader(file_or_content: Union[str, Path, TextIO, bytes]) -> csv.DictReader:
    """Normalize file path, string, bytes, or file-like object into a csv.DictReader."""
    if isinstance(file_or_content, bytes):
        text = file_or_content.decode("utf-8-sig", errors="replace")
        return csv.DictReader(io.StringIO(text))
    elif isinstance(file_or_content, Path) or (isinstance(file_or_content, str) and os.path.exists(file_or_content)):
        p = Path(file_or_content)
        if p.is_file():
            text = p.read_text(encoding="utf-8-sig", errors="replace")
            return csv.DictReader(io.StringIO(text))
        else:
            return csv.DictReader(io.StringIO(str(file_or_content)))
    elif isinstance(file_or_content, str):
        # Raw CSV string content
        return csv.DictReader(io.StringIO(file_or_content))
    elif hasattr(file_or_content, "read"):
        content = file_or_content.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8-sig", errors="replace")
        return csv.DictReader(io.StringIO(content))
    else:
        raise ValueError(f"Unsupported file format or source: {type(file_or_content)}")


# -----------------------------------------------------------------------------
# Parsers
# -----------------------------------------------------------------------------

def parse_orders_csv(source: Union[str, Path, TextIO, bytes]) -> List[Dict[str, Any]]:
    """Parse Internal OMS Orders CSV into domain model records."""
    reader = _get_reader(source)
    orders = []

    for idx, row in enumerate(reader, start=1):
        order_id = find_column_val(row, ["order_id", "order id", "orderId", "order_number", "ordernumber", "invoice_id", "id"])
        if not order_id:
            continue

        amount = clean_currency_str(find_column_val(row, ["order_amount", "amount", "gross_amount", "total_amount", "total_price", "price", "total"]))
        tax_amount = clean_currency_str(find_column_val(row, ["tax_amount", "tax", "gst", "tax_total", "cgst", "sgst"], default="0.00"))
        customer_id = find_column_val(row, ["customer_id", "customer id", "customerId", "user_id", "cust_id", "client_id"], default=f"CUST_{idx:03d}")
        status = find_column_val(row, ["status", "order_status", "state"], default="PAID").upper()
        created_at = find_column_val(row, ["created_at", "created at", "order_date", "date", "timestamp"], default="2026-09-01T10:00:00Z")

        model = InternalOrder(
            order_id=order_id,
            amount=amount,
            tax_amount=tax_amount,
            customer_id=customer_id,
            status=status,
            created_at=created_at,
        )
        orders.append(model.model_dump())

    return orders


def parse_settlements_csv(source: Union[str, Path, TextIO, bytes]) -> List[Dict[str, Any]]:
    """Parse Razorpay Settlement Dumps CSV into domain model records."""
    reader = _get_reader(source)
    settlements = []

    for idx, row in enumerate(reader, start=1):
        order_id = find_column_val(row, ["order_id", "order id", "orderId", "order_number", "ordernumber", "id"])
        payment_id = find_column_val(row, ["payment_id", "payment id", "paymentId", "pay_id", "transaction_id", "transactionid"], default=f"pay_{idx:04d}")
        if not order_id:
            continue

        gross_amount = clean_currency_str(find_column_val(row, ["gross_amount", "gross amount", "amount", "gross", "total_collected"]))
        fee = clean_currency_str(find_column_val(row, ["mdr_fee", "fee", "gateway_fee", "mdr", "service_fee"], default="0.00"))
        tax_on_fee = clean_currency_str(find_column_val(row, ["gst_on_fee", "tax_on_fee", "fee_tax", "gst", "tax", "service_tax"], default="0.00"))
        
        # Net amount calculation or extraction
        net_str = find_column_val(row, ["net_settlement_amount", "net_amount", "net amount", "net", "settlement_amount", "credit"])
        if net_str:
            net_amount = clean_currency_str(net_str)
        else:
            net_amount = quantize_currency(gross_amount - (fee + tax_on_fee))

        utr = find_column_val(row, ["payout_utr", "settlement_utr", "bank_utr", "utr", "reference_no"], default="")
        utr_val = utr if utr else None
        settled_at = find_column_val(row, ["settled_date", "settled_at", "settled at", "settlement_date", "date", "created_at"], default="2026-09-01T11:00:00Z")

        model = RazorpaySettlement(
            payment_id=payment_id,
            order_id=order_id,
            gross_amount=gross_amount,
            fee=fee,
            tax_on_fee=tax_on_fee,
            net_amount=net_amount,
            utr=utr_val,
            settled_at=settled_at,
        )
        settlements.append(model.model_dump())

    return settlements


def parse_bank_statements_csv(source: Union[str, Path, TextIO, bytes]) -> List[Dict[str, Any]]:
    """Parse Bank Statement Credits CSV into domain model records."""
    reader = _get_reader(source)
    bank_entries = []

    for idx, row in enumerate(reader, start=1):
        utr = find_column_val(row, ["utr_number", "bank_utr", "utr", "reference_no", "ref_no", "payout_utr", "txn_id", "chq_ref_no"])
        credit_amount = clean_currency_str(find_column_val(row, ["credit_amount", "credit amount", "credit", "amount", "deposit", "net_credit"]))
        bank_ref = find_column_val(row, ["bank_reference", "bank_ref", "bank ref", "ref", "reference", "id"], default=f"BNK_{idx:04d}")
        value_date = find_column_val(row, ["value_date", "value date", "date", "posting_date", "txn_date"], default="2026-09-01")
        description = find_column_val(row, ["description", "narration", "particulars", "remarks"], default=f"ACH CR RAZORPAY SETTLEMENT {utr}")

        if not utr:
            # Check if UTR is embedded in description
            utr_match = re.search(r"UTR[\w\d]+", description, re.IGNORECASE)
            if utr_match:
                utr = utr_match.group(0)

        if not utr:
            continue

        model = BankStatementEntry(
            bank_ref=bank_ref,
            utr=utr,
            credit_amount=credit_amount,
            value_date=value_date,
            description=description,
        )
        bank_entries.append(model.model_dump())

    return bank_entries


def load_csv_dataset(
    orders_source: Union[str, Path, bytes],
    settlements_source: Union[str, Path, bytes],
    bank_source: Union[str, Path, bytes],
) -> Dict[str, Any]:
    """Ingest all 3 CSV sources and return structured dataset dictionary."""
    orders = parse_orders_csv(orders_source)
    settlements = parse_settlements_csv(settlements_source)
    bank_entries = parse_bank_statements_csv(bank_source)

    return {
        "metadata": {
            "source": "csv_adapter",
            "total_internal_orders": len(orders),
            "total_settlements": len(settlements),
            "total_bank_entries": len(bank_entries),
        },
        "internal_orders": orders,
        "razorpay_settlements": settlements,
        "bank_statement_entries": bank_entries,
    }


def export_sample_csvs(output_dir: Optional[Union[str, Path]] = None) -> Dict[str, Path]:
    """
    Export the standardized 60-record benchmark batch into 3 realistic sample CSV files:
    - sample_orders.csv
    - sample_razorpay.csv
    - sample_bank.csv
    """
    import json
    target_dir = Path(output_dir) if output_dir else (REPO_ROOT / "data" / "samples")
    target_dir.mkdir(parents=True, exist_ok=True)

    json_path = get_dataset_path()
    if not json_path.exists():
        from data.generate_batch import generate_dataset
        generate_dataset(json_path)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    orders_file = target_dir / "sample_orders.csv"
    with open(orders_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Order ID", "Customer ID", "Order Amount (INR)", "Tax Amount", "Status", "Order Date"])
        for o in data.get("internal_orders", []):
            writer.writerow([o["order_id"], o["customer_id"], o["amount"], o["tax_amount"], o["status"], o["created_at"]])

    settlements_file = target_dir / "sample_razorpay.csv"
    with open(settlements_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Payment ID", "Order ID", "Gross Amount", "MDR Fee", "GST on Fee (18%)", "Net Settlement Amount", "Payout UTR", "Settled Date"])
        for s in data.get("razorpay_settlements", []):
            writer.writerow([s["payment_id"], s["order_id"], s["gross_amount"], s["fee"], s["tax_on_fee"], s["net_amount"], s["utr"] or "", s["settled_at"]])

    bank_file = target_dir / "sample_bank.csv"
    with open(bank_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Bank Reference", "UTR Number", "Credit Amount (INR)", "Value Date", "Description / Narration"])
        for b in data.get("bank_statement_entries", []):
            writer.writerow([b["bank_ref"], b["utr"], b["credit_amount"], b["value_date"], b["description"]])

    return {
        "orders_csv": orders_file,
        "settlements_csv": settlements_file,
        "bank_csv": bank_file,
    }


if __name__ == "__main__":
    paths = export_sample_csvs()
    print("Exported sample CSV files:")
    for k, v in paths.items():
        print(f"  - {k}: {v}")
