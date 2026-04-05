# Chapter 9: End-to-End Request Lifecycle

## Example question

Take this question:

"Which products have the highest refund rates and why are customers unhappy with them?"

## What happens step by step

1. The user enters the question in the frontend.
2. The frontend sends the request to the FastAPI backend.
3. The backend loads:
   - the system prompt
   - dbt-driven schema context
   - tool definitions
4. The model decides which tools are needed.
5. The backend executes:
   - SQL for structured refund metrics
   - vector search for complaint evidence
6. Tool outputs are fed back to the model.
7. The backend composes and normalizes the answer.
8. The frontend streams the answer back to the user.

## Why this lifecycle matters

This shows that the answer does not come from a single model call over arbitrary context.

It comes from a system that:

- has a semantic data layer
- has a retrieval layer
- has orchestration logic
- has output constraints

That is the real architecture of the project.

Referenced files:

- [api/main.py](/Users/akshayjain/Documents/chat_bot/api/main.py)
- [api/services/chat_service.py](/Users/akshayjain/Documents/chat_bot/api/services/chat_service.py)
- [frontend/src/lib/api.ts](/Users/akshayjain/Documents/chat_bot/frontend/src/lib/api.ts)
