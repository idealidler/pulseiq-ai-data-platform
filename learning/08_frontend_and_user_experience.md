# Chapter 8: Frontend and User Experience

## What the frontend does

The frontend is not only a chat box.

It has two purposes:

- present the project like a real product
- let users interact with the assistant

The main product tab includes:

- brand/header
- project framing
- benchmark KPIs
- prompt starter pack
- floating chat assistant

## Why the UI matters in this project

The goal is to demonstrate:

- data engineering depth
- AI functionality
- production-style user experience

That means the interface needs to feel intentional, not like a quick AI wrapper.

## Chat UX features already implemented

The chat UI supports:

- enter to send
- shift+enter for newline
- markdown answer rendering
- streaming responses
- compact floating assistant behavior
- rotating starter prompts

## Why streaming matters

Streaming improves perceived responsiveness.

Even when tool execution takes time, the user sees:

- status updates
- partial answer output

This reduces dead time and makes the assistant feel more responsive.

Referenced files:

- [frontend/src/App.tsx](/Users/akshayjain/Documents/chat_bot/frontend/src/App.tsx)
- [frontend/src/components/ProductTab.tsx](/Users/akshayjain/Documents/chat_bot/frontend/src/components/ProductTab.tsx)
- [frontend/src/lib/api.ts](/Users/akshayjain/Documents/chat_bot/frontend/src/lib/api.ts)
