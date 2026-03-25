dapr-ext-drasi extension
========================

This extension provides Drasi-trigger helpers for Dapr workflows.

Current milestone scope
-----------------------

- In-cluster provisioning only.
- Automatically creates a Drasi PostDaprPubSub reaction when ``@drasi_trigger`` is applied.
- Delegates route metadata to ``dapr_agents.workflow.decorators.message_router``.
- Subscription wiring is handled by ``AgentRunner.subscribe(...)`` / ``AgentRunner.serve(...)`` from ``dapr-agents``.
- Uses the in-cluster Drasi API endpoint:

  - http://drasi-api.drasi-system.svc.cluster.local:8080

- Idempotent creation by convention:

  - Topic: ``{query_id}_reaction_agents``
  - Reaction: ``{query_id}-reaction-agents``

  If a reaction with the convention name already exists, it is not recreated.


Install in a venv
-----------------

::

    python -m venv .venv
    source .venv/bin/activate
    pip install -U pip
    pip install dapr-ext-workflow dapr dapr-agents
    pip install dapr-ext-drasi


Developer release to PyPI (manual CLI)
---------------------------------------

From this folder:

::

    cd python-sdk/ext/dapr-ext-drasi

1) Bump version in ``dapr/ext/drasi/version.py`` (keep ``.dev`` for dev streams).

2) Build distributions:

::

    python -m pip install -U build twine
    python -m build

3) Upload (token auth):

::

    export TWINE_USERNAME=__token__
    export TWINE_PASSWORD=<your-pypi-token>
    python -m twine upload dist/*

4) Validate install from your account release:

::

    pip install -U dapr-ext-drasi==<your-dev-version>


Example
-------

See:

- ``examples/01_drasi_trigger_workflow.py``

Run:

::

    python examples/01_drasi_trigger_workflow.py

Expected behavior:

- Registers orchestrator workflow and activity.
- Ensures reaction for ``query_id="critical-tickets"`` (create if missing, skip if exists).
- ``AgentRunner.subscribe(...)`` wires pub/sub and schedules workflow executions from Drasi events.


Decorator usage
---------------

::

    from dapr.ext.drasi import drasi_trigger, DrasiChangeEvent
    from dapr.ext.workflow import DaprWorkflowContext

    @drasi_trigger(query_id="critical-tickets", pubsub="notifications-pubsub")
    def on_change(ctx: DaprWorkflowContext, event: DrasiChangeEvent):
        for ticket in event.added_results:
            ...


Notes
-----

- Set ``provision_reaction=False`` in ``@drasi_trigger`` if you want to disable automatic Drasi API calls in local tests.
- Set ``fail_on_provision_error=True`` if provisioning failures should fail fast instead of logging a warning.

