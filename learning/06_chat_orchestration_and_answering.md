# Chapter 6: Chat Orchestration and Answering

## What the orchestration layer does

The orchestration layer decides how to answer a user question.

It lives mainly in:

- `api/services/chat_service.py`

Its responsibilities are:

- load the system prompt
- inject dbt-driven schema context
- define the tools
- call the model
- execute tool calls
- loop until the model produces a final answer

## The three answer paths

The assistant can respond through:

- SQL only
- vector search only
- hybrid

### SQL only

Used for:

- rankings
- metrics
- revenue
- refund counts
- product sales

### Vector only

Used for:

- complaint themes
- customer language
- semantic issue exploration

### Hybrid

Used when both are needed, for example:

- "Which products have the lowest CSAT and what are customers saying?"
- "Which products have the highest refund rates and why are customers unhappy?"

## Why the system prompt matters

The system prompt defines:

- tool selection rules
- grounding rules
- output contract
- SQL constraints

But the prompt is not the only source of meaning anymore.
It is now supplemented by dbt-driven schema context at runtime.

## How tool execution works

The model produces tool calls.

The backend then:

1. parses the tool arguments
2. runs the tool
3. appends the tool output back into the model conversation
4. continues until no more tool calls are needed

This is what makes the assistant tool-using rather than just conversational.

## Why answer formatting is handled carefully

The backend also normalizes answer structure and, in hybrid cases, may compose a more grounded response format.

This is important because:

- raw model output can be loose
- hybrid answers must keep structured metrics separate from semantic evidence

Referenced files:

- [api/services/chat_service.py](/Users/akshayjain/Documents/chat_bot/api/services/chat_service.py)
- [api/services/sql_service.py](/Users/akshayjain/Documents/chat_bot/api/services/sql_service.py)
- [api/services/vector_service.py](/Users/akshayjain/Documents/chat_bot/api/services/vector_service.py)
