export type ChatResponse = {
  answer: string;
  route: string;
  evidence: Array<Record<string, unknown>>;
  debug?: Record<string, unknown> | null;
};

type StreamHandlers = {
  onStatus?: (message: string) => void;
  onAnswerDelta?: (delta: string) => void;
  onComplete?: (payload: Omit<ChatResponse, "answer">) => void;
  onError?: (message: string) => void;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function askPulseIQ(question: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    throw new Error(`Chat request failed with status ${response.status}`);
  }

  return response.json() as Promise<ChatResponse>;
}

export async function streamPulseIQ(question: string, handlers: StreamHandlers): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok || !response.body) {
    throw new Error(`Streaming chat request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const rawEvent of events) {
      const lines = rawEvent.split("\n");
      const eventType = lines.find((line) => line.startsWith("event:"))?.replace("event:", "").trim();
      const dataLine = lines.find((line) => line.startsWith("data:"))?.replace("data:", "").trim();
      if (!eventType || !dataLine) {
        continue;
      }

      const payload = JSON.parse(dataLine) as Record<string, unknown>;
      if (eventType === "status") {
        handlers.onStatus?.(String(payload.message ?? ""));
      } else if (eventType === "answer_delta") {
        handlers.onAnswerDelta?.(String(payload.delta ?? ""));
      } else if (eventType === "complete") {
        handlers.onComplete?.({
          route: String(payload.route ?? "unknown"),
          evidence: Array.isArray(payload.evidence) ? (payload.evidence as Array<Record<string, unknown>>) : [],
          debug: (payload.debug as Record<string, unknown> | null | undefined) ?? null,
        });
      } else if (eventType === "error") {
        handlers.onError?.(String(payload.message ?? "Unknown stream error"));
      }
    }
  }
}
