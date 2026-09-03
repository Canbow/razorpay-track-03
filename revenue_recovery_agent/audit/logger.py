"""Atomic JSON Lines audit logger for recovery agent compliance and auditing."""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union
from decimal import Decimal

from revenue_recovery_agent.core.models import AuditLogRecord


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to properly serialize Decimal types to float or string."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class AuditLogger:
    """
    Thread-safe, atomic JSON Lines audit logger.
    Records every diagnostic, guard evaluation, and action outcome with microsecond timestamps.
    """
    _lock = threading.Lock()

    def __init__(self, log_file: Optional[Union[str, Path]] = None):
        if log_file is None:
            # Default to recovery_audit_trail.jsonl in current working directory or repo root
            self.log_file = Path("recovery_audit_trail.jsonl").resolve()
        else:
            self.log_file = Path(log_file).resolve()
            
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, record: AuditLogRecord) -> None:
        """Append an AuditLogRecord to the JSONL log file atomically."""
        line = json.dumps(record.model_dump(), cls=DecimalEncoder)
        with self._lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def log_event(
        self,
        invoice_id: str,
        event_type: str,
        action: str,
        guard_check_passed: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLogRecord:
        """Create and write an audit record with current microsecond ISO timestamp."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        record = AuditLogRecord(
            timestamp=now_str,
            invoice_id=invoice_id,
            event_type=event_type,
            action=action,
            guard_check_passed=guard_check_passed,
            details=details or {},
        )
        self.log(record)
        return record
