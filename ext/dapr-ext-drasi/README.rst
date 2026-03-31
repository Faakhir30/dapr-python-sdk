dapr-ext-drasi extension
========================

This extension provides Drasi-trigger helpers for Dapr workflows.

Current milestone scope
-----------------------

- In-cluster provisioning only.
- Optionally creates or updates a **SmartRouter** reaction when ``@drasi_trigger`` is applied (merges ``query_id`` into the same reaction id when multiple handlers share ``reaction_name``).
- Delegates route metadata to ``dapr_agents.workflow.decorators.message_router``.
- Subscription wiring is handled by ``AgentRunner.subscribe(...)`` / ``AgentRunner.serve(...)`` from ``dapr-agents``.
- Uses the in-cluster Drasi API endpoint:

  - http://drasi-api.drasi-system.svc.cluster.local:8080

- Idempotent creation by convention:

  - Topic: ``{query_id}_reaction_agents``
  - SmartRouter reaction id: ``{query_id}-smart-router`` (override with ``reaction_name=``).



Install in a venv
-----------------

::

    python -m venv .venv
    source .venv/bin/activate
    pip install -U pip
    pip install dapr-ext-drasi



Example
-------

See:

- ``examples/01_drasi_trigger_workflow.py``
- ``examples/02_durable_agent_smart_router.py``

Run:

Prerequisites:

- K8s cluster running (e.g., k3d cluster)
- Drasi platform installed (including Dapr)
- https://github.com/drasi-project/learning project running

project should be running at http://localhost:8123 already.

::

    cd examples
    docker build -t drasi-dapr-agents .
    dapr run -k -f dapr-k8s-workflow.yaml

Open a new terminal and run:

::

    cd learning/tutorial/dapr/demo
    ./demo-notifications-service.sh

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


SmartRouter ToolSet (dynamic subscriptions)
-------------------------------------------

This extension also includes ``DrasiSmartRouterToolSet`` for dynamic, per-instance subscriptions.

Use case:

- ``@drasi_trigger`` handles static trigger subscriptions known at development time.
- ``DrasiSmartRouterToolSet`` handles runtime query discovery and subscribe/unsubscribe for a specific agent run (for example by using ``ctx.instance_id`` as topic).

Example:

::

    from dapr.ext.drasi import DrasiSmartRouterToolSet

    toolset = DrasiSmartRouterToolSet(
        smart_router_url="http://smart-router.drasi-system.svc.cluster.local",
        instance_id=ctx.instance_id,
    )
    tools = toolset.get_tools()

Provided tools:

- ``drasi_list_queries``
- ``drasi_subscribe_query``
- ``drasi_unsubscribe_query``
- ``drasi_list_subscriptions``

``drasi_subscribe_query`` also accepts optional ``pubsub_name``, ``output_format`` (``Unpacked`` / ``Packed``), and ``skip_control_signals`` (True, False), matching SmartRouter ``POST /subscriptions``.

