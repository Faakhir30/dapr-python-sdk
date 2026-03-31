from __future__ import annotations

import asyncio

import dapr.ext.workflow as wf

from dapr.ext.drasi import DrasiChangeEvent, drasi_trigger
from dapr.clients import DaprClient

from dapr_agents.workflow.utils.core import wait_for_shutdown
from dapr_agents.workflow.utils.registration import register_message_routes


@drasi_trigger(query_id="low-stock-event-query", pubsub="notifications-pubsub")
def on_change(ctx: wf.DaprWorkflowContext, event: DrasiChangeEvent):
    print(f"Recieved event", event, flush=True)
    print(f"Processing ticket: {event.after} from {event.source}", flush=True)

    return {
        "query_id": event.query_id,
        "processed": len(event.added_results),
    }


async def main() -> None:
    runtime = wf.WorkflowRuntime()
    runtime.register_workflow(on_change)
    runtime.start()

    try:
        with DaprClient() as client:
            closers = register_message_routes(targets=[on_change], dapr_client=client)
            try:
                await wait_for_shutdown()
            finally:
                for close in closers:
                    try:
                        close()
                    except Exception:
                        pass
    finally:
        runtime.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
