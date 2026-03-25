# -*- coding: utf-8 -*-

from __future__ import annotations

import inspect
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

from dapr_agents.workflow.decorators import message_router

from dapr.ext.drasi.provisioning import (
    DrasiProvisioner,
    DrasiReactionPlan,
    reaction_name_for_query,
    topic_name_for_query,
)
from dapr.ext.drasi.types import DrasiChangeEvent

R = TypeVar("R")
logger = logging.getLogger(__name__)


def drasi_trigger(
    *,
    query_id: str,
    pubsub: str,
    topic: Optional[str] = None,
    reaction_name: Optional[str] = None,
    provision_reaction: bool = True,
    fail_on_provision_error: bool = False,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    if not query_id:
        raise ValueError("query_id is required")
    if not pubsub:
        raise ValueError("pubsub is required")

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        signature = inspect.signature(func)
        params = list(signature.parameters.keys())

        if len(params) < 2:
            raise ValueError("drasi_trigger target must accept ctx and event arguments")

        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            bound = signature.bind_partial(*args, **kwargs)
            raw_event = bound.arguments.get("event")
            if raw_event is not None and not isinstance(raw_event, DrasiChangeEvent):
                if not isinstance(raw_event, dict):
                    raise TypeError(
                        f"Expected event payload dict for parameter 'event', got {type(raw_event)!r}"
                    )
                bound.arguments["event"] = DrasiChangeEvent.from_payload(raw_event)
            return func(*bound.args, **bound.kwargs)

        resolved_topic = topic or topic_name_for_query(query_id)
        resolved_reaction_name = reaction_name or reaction_name_for_query(query_id)

        trigger_data: Dict[str, Any] = {
            "query_id": query_id,
            "pubsub": pubsub,
            "topic": resolved_topic,
            "reaction_name": resolved_reaction_name,
        }

        if provision_reaction:
            try:
                provisioner = DrasiProvisioner()
                provisioner.ensure_post_dapr_pubsub_reaction(
                    plan=DrasiReactionPlan(
                        query_id=query_id,
                        pubsub_name=pubsub,
                        topic_name=resolved_topic,
                        reaction_name=resolved_reaction_name,
                    )
                )
            except Exception as exc:
                if fail_on_provision_error:
                    raise
                logger.warning(
                    "Failed to ensure Drasi reaction '%s' for query '%s': %s",
                    resolved_reaction_name,
                    query_id,
                    exc,
                )

        routed = message_router(
            pubsub=pubsub,
            topic=resolved_topic,
            message_model=DrasiChangeEvent,
        )(wrapped)

        setattr(routed, "_is_drasi_trigger", True)
        setattr(routed, "_drasi_trigger_data", trigger_data)
        return routed

    return decorator
