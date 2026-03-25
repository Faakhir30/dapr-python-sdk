from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import error, request

DEFAULT_DRASI_API_URL = "http://drasi-api.drasi-system.svc.cluster.local:8080"


@dataclass(frozen=True)
class DrasiReactionPlan:
    query_id: str
    pubsub_name: str
    topic_name: str
    reaction_name: str


class DrasiProvisioner:
    def __init__(
        self, base_url: str = DEFAULT_DRASI_API_URL, timeout: float = 10.0
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def ensure_post_dapr_pubsub_reaction(self, plan: DrasiReactionPlan) -> bool:
        if self.reaction_exists(plan.reaction_name):
            return False

        spec = {
            "kind": "PostDaprPubSub",
            "queries": {
                plan.query_id: json.dumps(
                    {
                        "pubsubName": plan.pubsub_name,
                        "topicName": plan.topic_name,
                        "format": "Unpacked",
                        "skipControlSignals": True,
                    }
                )
            },
        }
        self._request(
            method="PUT",
            path=f"/v1/reactions/{plan.reaction_name}",
            body=spec,
        )
        return True

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
    return f"{normalize_name(query_id)}-topic"


def reaction_name_for_query(query_id: str) -> str:
    return f"{normalize_name(query_id)}-agents"
