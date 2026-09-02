"""Structured JSON Lines audit logger with atomic file writes and Decimal serialization."""
import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from core.models import AuditLogEntry


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to properly serialize Decimals, Enums, and datetimes."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class AuditLogger:
    """Thread-safe and atomic JSONL logger for financial audit trail."""

    def __init__(self, log_path: Union[str, Path] = "audit_trail.jsonl"):
        self.log_path = Path(log_path)
        self._entries: List[AuditLogEntry] = []

    def create_entry(
        self,
        order_id: str,
        step: str,
        action_taken: str,
        math_verified: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLogEntry:
        """Create and record a structured audit log entry."""
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            order_id=order_id,
            step=step,
            action_taken=action_taken,
            math_verified=math_verified,
            details=details or {},
        )
        self.log(entry)
        return entry

    def log(self, entry: Union[AuditLogEntry, Dict[str, Any]]) -> None:
        """Append an entry to in-memory records and write to file."""
        if isinstance(entry, dict):
            entry_obj = AuditLogEntry(**entry)
        else:
            entry_obj = entry

        self._entries.append(entry_obj)
        self._append_to_file(entry_obj)

    def _append_to_file(self, entry: AuditLogEntry) -> None:
        """Append a single record atomically to the JSONL log file."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry.model_dump(), cls=DecimalEncoder) + "\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line)

    def get_entries(self) -> List[AuditLogEntry]:
        """Return all in-memory audit log entries."""
        return list(self._entries)

    def write_all(self, file_path: Optional[Union[str, Path]] = None) -> None:
        """Rewrite all stored entries to the target file."""
        target_file = Path(file_path) if file_path else self.log_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file = target_file.with_suffix(".tmp")

        with open(temp_file, "w", encoding="utf-8") as f:
            for entry in self._entries:
                f.write(json.dumps(entry.model_dump(), cls=DecimalEncoder) + "\n")

        os.replace(temp_file, target_file)

    def clear(self) -> None:
        """Clear memory and remove log file if exists."""
        self._entries.clear()
        if self.log_path.exists():
            self.log_path.unlink()
