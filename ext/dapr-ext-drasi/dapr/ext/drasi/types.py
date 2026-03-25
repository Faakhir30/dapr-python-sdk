# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional


@dataclass
class DrasiEventPayload:
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    source: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DrasiChangeEvent:
    op: Literal["i", "u", "d"]
    payload: DrasiEventPayload
    seq: int = 0
    ts_ms: int = 0

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "DrasiChangeEvent":
        if not isinstance(payload, dict):
            raise TypeError("DrasiChangeEvent payload must be a dictionary")
        return cls(
            op=str(payload.get("op", "")),
            payload=DrasiEventPayload(**payload.get("payload", {}) or {}),
            seq=payload.get("seq", 0),
            ts_ms=payload.get("ts_ms", 0),
        )

    @property
    def source(self) -> Dict[str, Any]:
        value = self.payload.source
        return value if isinstance(value, dict) else {}

    @property
    def query_id(self) -> str:
        return str(self.source.get("queryId", self.source.get("query_id", "")))

    @property
    def source_ts_ms(self) -> Optional[int]:
        value = self.source.get("ts_ms", self.source.get("sourceTimeMs"))
        if value is None:
            return None
        try:
            return int(value)
        except Exception:
            return None

    @property
    def before(self) -> Optional[Dict[str, Any]]:
        return self.payload.before

    @property
    def after(self) -> Optional[Dict[str, Any]]:
        return self.payload.after

    def to_workflow_input(self) -> Dict[str, Any]:
        return {
            "op": self.op,
            "payload": self.payload.__dict__,
            "seq": self.seq,
            "ts_ms": self.ts_ms,
        }

    def __str__(self):
        s = ""
        if self.query_id:
            s += f"\nsource: {self.query_id}\n"
        if self.before:
            s += f"before: {self.before}\n"
        if self.after:
            s += f"after: {self.after}\n"
        return s
