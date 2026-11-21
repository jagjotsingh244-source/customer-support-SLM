"""Shared setup for the generation experiments."""

MID = "Qwen/Qwen3.5-2B"
SYSTEM = "You are Nova, NimbusCart's support assistant."
USER = "Hi, where is my order 4417?"


def fn(name, description, props=None, required=None):
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": props or {}, "required": required or []}}}


# One tool, for the single-tool experiments.
ORDER_STATUS = fn("get_order_status", "Status of one of the signed-in customer's orders",
                  {"order_id": {"type": "integer"}}, ["order_id"])

# Draft of Nova's full tool set, from the DESIGN.md capability map (names and fields will change when the tool layer is built).
NOVA_TOOLS = [
    fn("list_orders", "List the signed-in customer's recent orders",
       {"limit": {"type": "integer", "description": "How many orders to return"}}),
    ORDER_STATUS,
    fn("get_tracking", "Carrier, tracking number and delivery estimate for one of the signed-in customer's orders",
       {"order_id": {"type": "integer"}}, ["order_id"]),
    fn("start_return", "Start a return for an item in one of the signed-in customer's orders. Only call after the customer confirms.",
       {"order_id": {"type": "integer"}, "item_id": {"type": "integer"},
        "reason": {"type": "string", "description": "The customer's reason, in their words"}},
       ["order_id", "item_id", "reason"]),
    fn("get_refund_status", "Status and amount of a refund for one of the signed-in customer's orders",
       {"order_id": {"type": "integer"}}, ["order_id"]),
    fn("escalate_to_human", "Hand the conversation to a human agent",
       {"summary": {"type": "string", "description": "One-sentence summary of the issue for the agent"}}, ["summary"]),
]


def messages(system=SYSTEM, user=USER):
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
