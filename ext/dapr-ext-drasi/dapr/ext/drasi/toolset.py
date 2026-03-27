from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib import request

from dapr_agents.tool import AgentTool, tool


def _http_json(
    *,
    method: str,
    url: str,
    body: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url=url, data=data, method=method, headers=headers)
    with request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))


@dataclass
class DrasiSmartRouterToolSet:
    smart_router_url: str
    instance_id: str
    timeout: float = 10.0

    def __post_init__(self) -> None:
        base = self.smart_router_url.rstrip("/")
        self.smart_router_url = base

    def get_tools(self) -> List[AgentTool]:
        timeout = self.timeout
        base_url = self.smart_router_url
        instance_id = self.instance_id

        @tool
        async def drasi_list_queries() -> Dict[str, Any]:
            """List SmartRouter queries with descriptions."""
            return _http_json(
                method="GET",
                url=f"{base_url}/queries",
                timeout=timeout,
            )

        @tool
        async def drasi_subscribe_query(query_id: str, topic: Optional[str] = None) -> Dict[str, Any]:
            """Subscribe instance topic (or explicit topic) to a Drasi query."""
            target_topic = topic or instance_id
            return _http_json(
                method="POST",
                url=f"{base_url}/subscriptions",
                body={"queryId": query_id, "topic": target_topic},
                timeout=timeout,
            )

        @tool
        async def drasi_unsubscribe_query(
            query_id: str, topic: Optional[str] = None
        ) -> Dict[str, Any]:
            """Unsubscribe instance topic (or explicit topic) from a Drasi query."""
            target_topic = topic or instance_id
            return _http_json(
                method="DELETE",
                url=f"{base_url}/subscriptions",
                body={"queryId": query_id, "topic": target_topic},
                timeout=timeout,
            )

        @tool
        async def drasi_list_subscriptions(query_id: Optional[str] = None) -> Dict[str, Any]:
            """List active query subscriptions by topic."""
            url = f"{base_url}/subscriptions"
            if query_id:
                url = f"{url}?queryId={query_id}"
            return _http_json(method="GET", url=url, timeout=timeout)

        return [
            drasi_list_queries,
            drasi_subscribe_query,
            drasi_unsubscribe_query,
            drasi_list_subscriptions,
        ]
