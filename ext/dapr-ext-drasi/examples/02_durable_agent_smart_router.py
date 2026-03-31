from __future__ import annotations

import asyncio

import dapr.ext.workflow as wf
from dapr_agents.workflow.runners.agent import AgentRunner

from dapr.ext.drasi import (
    DrasiChangeEvent,
    DrasiSmartRouterToolSet,
    drasi_trigger,
)
from dapr.clients import DaprClient

from dapr_agents.llm import DaprChatClient

from dapr_agents import DurableAgent
from dapr_agents.agents.configs import (
    AgentMemoryConfig,
    AgentPubSubConfig,
    AgentStateConfig,
    AgentRegistryConfig,
)
from dapr_agents.memory import ConversationDaprStateMemory
from dapr_agents.storage.daprstores.stateservice import StateStoreService
from dapr_agents.workflow.utils.core import wait_for_shutdown
from dapr_agents.workflow.utils.registration import register_message_routes
from dapr_agents import call_agent


@drasi_trigger(query_id="low-stock-event-query", pubsub="notifications-pubsub")
async def on_change(ctx: wf.DaprWorkflowContext, event: DrasiChangeEvent):
    print(f"Recieved event", event, flush=True)
    print(f"Processing ticket: {event.after} from {event.source}", flush=True)
    # TODO: "smart_router_url" is auto-overriden at at runtime by decorator 
    # (hacky way of passing router_url inside on_change, will add a proper utill in extension)
    toolset = DrasiSmartRouterToolSet(
        smart_router_url="http://smart-router.drasi-system.svc.cluster.local",
        instance_id=ctx.instance_id,
    )
    tools = toolset.get_tools()

    agent = DurableAgent(
        name="SmartRouterAgent",
        role="Inventory Assistant",
        instructions = [
            "You will receive low-stock events for products. Your goal is to determine whether the product has already been approved by a human."
            "First, use the `drasi_list_queries` tool to discover available queries. Carefully read their descriptions to identify the query related to human approvals."
            "Select the most relevant query for human approvals and subscribe to it."
            "After subscribing, use the `drasi_get_results` tool to retrieve results from that query."
            "Inspect the results to check whether the product from the low-stock event has been approved by a human."
            "If a matching human approval is found:",
            "- Unsubscribe from the query you subscribed to.",
            "- Return a clear message: 'Human approval found for this product. Increasing stock.'"
            "If no approval is found, do not take action and return nothing or a minimal response indicating no approval."
            "Only act on the specific product in the incoming event. Do not process unrelated products."
            "Avoid unnecessary tool calls. Be efficient and only subscribe to one relevant query."
        ],
        tools=tools,
        llm=DaprChatClient(component_name="openai-chat-component"),
        memory=AgentMemoryConfig(
            store=ConversationDaprStateMemory(
                store_name="agent-memory",
            )
        ),
        state=AgentStateConfig(
            store=StateStoreService(store_name="agent-workflow"),
        ),
        registry=AgentRegistryConfig(
            store=StateStoreService(store_name="agent-registry"),
        ),
    )
    return agent.agent_workflow(ctx, { "task": event.after })

    
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
