from urllib.error import HTTPError

from dapr.ext.drasi.provisioning import (
    DrasiProvisioner,
    DrasiReactionPlan,
    reaction_name_for_query,
    topic_name_for_query,
)


def test_topic_and_reaction_naming_convention():
    assert (
        topic_name_for_query("critical-tickets") == "critical-tickets_reaction_agents"
    )
    assert (
        reaction_name_for_query("critical-tickets")
        == "critical-tickets-reaction-agents"
    )


def test_ensure_reaction_skips_when_exists(monkeypatch):
    provisioner = DrasiProvisioner()

    def fake_request(*, method, path, body=None):
        assert method == "GET"
        return {"id": "existing"}

    monkeypatch.setattr(provisioner, "_request", fake_request)
    created = provisioner.ensure_post_dapr_pubsub_reaction(
        DrasiReactionPlan(
            query_id="critical-tickets",
            pubsub_name="notifications-pubsub",
            topic_name="critical-tickets_reaction_agents",
            reaction_name="critical-tickets-reaction-agents",
        )
    )
    assert created is False


def test_ensure_reaction_creates_when_missing(monkeypatch):
    provisioner = DrasiProvisioner()
    calls = []

    def fake_request(*, method, path, body=None):
        calls.append((method, path, body))
        if method == "GET":
            raise HTTPError(url=path, code=404, msg="not found", hdrs=None, fp=None)
        return {"id": "created"}

    monkeypatch.setattr(provisioner, "_request", fake_request)
    created = provisioner.ensure_post_dapr_pubsub_reaction(
        DrasiReactionPlan(
            query_id="critical-tickets",
            pubsub_name="notifications-pubsub",
            topic_name="critical-tickets_reaction_agents",
            reaction_name="critical-tickets-reaction-agents",
        )
    )

    assert created is True
    assert calls[0][0] == "GET"
    assert calls[1][0] == "PUT"
    assert calls[1][2]["kind"] == "PostDaprPubSub"
