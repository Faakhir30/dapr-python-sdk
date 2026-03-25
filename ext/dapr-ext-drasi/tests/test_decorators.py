from dapr.ext.drasi import DrasiChangeEvent, drasi_trigger


@drasi_trigger(
    query_id="critical-tickets",
    pubsub="notifications-pubsub",
    provision_reaction=False,
)
def sample_workflow(ctx, event):
    return event


def test_drasi_trigger_attaches_metadata():
    data = getattr(sample_workflow, "_drasi_trigger_data")
    assert data["query_id"] == "critical-tickets"
    assert data["pubsub"] == "notifications-pubsub"
    assert data["topic"] == "critical-tickets_reaction_agents"

    router_data = getattr(sample_workflow, "_message_router_data")
    assert router_data["pubsub"] == "notifications-pubsub"
    assert router_data["topic"] == "critical-tickets_reaction_agents"


def test_drasi_trigger_converts_event_payload():
    event = sample_workflow(
        None,
        {
            "op": "i",
            "payload": {
                "after": {"id": 1},
                "source": {"queryId": "critical-tickets", "ts_ms": 123},
            },
            "seq": 10,
            "ts_ms": 456,
        },
    )

    assert isinstance(event, DrasiChangeEvent)
    assert event.op == "i"
    assert event.query_id == "critical-tickets"
    assert event.after["id"] == 1
