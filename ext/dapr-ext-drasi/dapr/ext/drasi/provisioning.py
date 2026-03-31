from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import error, request

DEFAULT_DRASI_API_URL = "http://drasi-api.drasi-system.svc.cluster.local:8080"


@dataclass(frozen=True)
class DrasiSmartRouterPlan:
    """Provision or merge a query into a SmartRouter reaction via Drasi management API."""
    reaction_name: str
    pubsub_name: str
    query_id: str
    query_description: Optional[str] = None


class DrasiProvisioner:
    def __init__(
        self, base_url: str = DEFAULT_DRASI_API_URL, timeout: float = 10.0
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def ensure_smart_router_reaction(self, plan: DrasiSmartRouterPlan) -> bool:
        """
        Create or update a SmartRouter reaction so ``plan.query_id`` is registered.

        Merges into existing ``queries`` when the reaction already exists (same
        ``reaction_name``, multiple ``@drasi_trigger`` handlers / query IDs).
        """
        query_blob = self._smart_router_query_blob(plan)
        path = f"/v1/reactions/{plan.reaction_name}"

        existing_spec: Optional[Dict[str, Any]] = None
        try:
            dto = self._request(method="GET", path=path)
            existing_spec = dto.get("spec") if isinstance(dto, dict) else None
        except error.HTTPError as exc:
            if exc.code != 404:
                raise

        queries: Dict[str, str] = {}
        if existing_spec and isinstance(existing_spec.get("queries"), dict):
            queries = {
                str(k): str(v) if v is not None else ""
                for k, v in existing_spec["queries"].items()
            }

        kind = (existing_spec or {}).get("kind") or "SmartRouter"
        if existing_spec and kind != "SmartRouter":
            raise ValueError(
                f"Reaction '{plan.reaction_name}' exists with kind {kind!r}; "
                "expected SmartRouter for drasi_trigger provisioning."
            )

        queries[plan.query_id] = query_blob

        properties: Dict[str, Any] = {}
        if existing_spec and isinstance(existing_spec.get("properties"), dict):
            properties = dict(existing_spec["properties"])
        if "pubsubName" not in properties:
            properties["pubsubName"] = plan.pubsub_name

        spec = {
            "kind": "SmartRouter",
            "properties": properties,
            "queries": queries,
        }
        self._request(method="PUT", path=path, body=spec)
        return True

    @staticmethod
    def _smart_router_query_blob(plan: DrasiSmartRouterPlan) -> str:
        desc = plan.query_description or f"Drasi query `{plan.query_id}` (dapr.ext.drasi)"
        cfg = {
            "description": desc,
            "defaultFormat": "Unpacked",
            "defaultSkipControlSignals": True,
            "defaultPubsubName": plan.pubsub_name,
        }
        return json.dumps(cfg)

    def reaction_exists(self, reaction_name: str) -> bool:
        try:
            self._request(method="GET", path=f"/v1/reactions/{reaction_name}")
            return True
        except error.HTTPError as exc:
            if exc.code == 404:
                return False
            raise

    def _request(
        self, *, method: str, path: str, body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(
            url=f"{self._base_url}{path}",
            data=data,
            method=method,
            headers=headers,
        )

        with request.urlopen(req, timeout=self._timeout) as response:
            raw = response.read()
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))


def normalize_name(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]", "-", value.strip())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized.lower()


def topic_name_for_query(query_id: str) -> str:
    """Dapr pub/sub topic for this workflow handler (agent instance / convention)."""
    return f"{normalize_name(query_id)}_reaction_agents"


def reaction_name_for_query(query_id: str) -> str:
    return f"{normalize_name(query_id)}-smart-router"
