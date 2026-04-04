import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  Bot,
  Database,
  LineChart,
  LoaderCircle,
  MessageSquare,
  Minus,
  Radar,
  Server,
  Sparkles,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { streamPulseIQ } from "../lib/api";

type Message = {
  role: "user" | "assistant";
  text: string;
  route?: string;
  status?: string;
};

const prompts = [
  "Which products have the highest risk score and what are customers complaining about?",
  "Which categories have the highest refund rate recently?",
  "What are customers saying about battery issues in electronics?",
];

const stats = [
  { label: "Context windows used", value: "1", icon: LineChart },
  { label: "Tokens used end to end", value: "160K", icon: Radar },
  { label: "Prompting style", value: "Tight, iterative, low waste", icon: Bot },
  { label: "Build stack shipped", value: "DuckDB + dbt + Qdrant", icon: Database },
];

const featureCards = [
  {
    title: "Data platform first",
    body: "Synthetic sources, raw Parquet, DuckDB, dbt marts, embeddings, evals. The chatbot is the interface, not the whole story.",
  },
  {
    title: "Honest product framing",
    body: "The tone is playful on purpose. The implementation underneath is very real and intentionally modeled like a production-grade system.",
  },
  {
    title: "Evidence over vibes",
    body: "SQL handles metrics, vector search handles customer language, and hybrid answers only happen when both kinds of evidence are needed.",
  },
];

export function ProductTab() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      text: "Welcome to the part where a learning project got unreasonably serious. Ask about risk, refunds, complaint themes, or operational weirdness.",
      route: "system",
    },
  ]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!chatOpen) {
      return;
    }
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, chatOpen]);

  async function submitQuestion(nextQuestion?: string) {
    const prompt = (nextQuestion ?? question).trim();
    if (!prompt || loading) {
      return;
    }

    setMessages((current) => [...current, { role: "user", text: prompt }]);
    setQuestion("");
    setLoading(true);
    const assistantIndexRef = { current: -1 };

    setMessages((current) => {
      assistantIndexRef.current = current.length;
      return [
        ...current,
        {
          role: "assistant",
          text: "",
          route: "thinking",
          status: "Opening the pipeline...",
        },
      ];
    });

    try {
      await streamPulseIQ(prompt, {
        onStatus: (status) => {
          setMessages((current) =>
            current.map((message, index) =>
              index === assistantIndexRef.current ? { ...message, status } : message,
            ),
          );
        },
        onAnswerDelta: (delta) => {
          setMessages((current) =>
            current.map((message, index) =>
              index === assistantIndexRef.current
                ? { ...message, text: `${message.text}${delta}` }
                : message,
            ),
          );
        },
        onComplete: (payload) => {
          setMessages((current) =>
            current.map((message, index) =>
              index === assistantIndexRef.current
                ? { ...message, route: payload.route, status: undefined }
                : message,
            ),
          );
        },
        onError: (message) => {
          setMessages((current) =>
            current.map((entry, index) =>
              index === assistantIndexRef.current
                ? {
                    ...entry,
                    text: `I couldn't reach the backend cleanly. ${message}`,
                    route: "error",
                    status: undefined,
                  }
                : entry,
            ),
          );
        },
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setMessages((current) =>
        current.map((entry, index) =>
          index === assistantIndexRef.current
            ? {
                ...entry,
                text: `I couldn't reach the backend cleanly. ${message}`,
                route: "error",
                status: undefined,
              }
            : entry,
        ),
      );
    } finally {
      setLoading(false);
    }
  }

  function handlePromptClick(prompt: string) {
    setChatOpen(true);
    void submitQuestion(prompt);
  }

  function handleQuestionKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submitQuestion();
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(255,107,44,0.16),_transparent_32%),radial-gradient(circle_at_85%_10%,_rgba(15,92,75,0.16),_transparent_26%),linear-gradient(180deg,_rgba(255,255,255,0.5),_rgba(244,239,230,0.85))]" />
      <div className="absolute inset-0 bg-grid bg-[length:42px_42px] opacity-20" />

      <div className="relative mx-auto max-w-7xl px-6 pb-24 pt-10 md:px-10">
        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-[2.5rem] border border-ink/10 bg-ink px-8 py-10 text-shell shadow-panel">
            <div className="flex flex-wrap items-center gap-3 text-xs uppercase tracking-[0.26em] text-shell/60">
              <Server className="h-4 w-4" />
              Self-aware product demo
            </div>
            <h1 className="mt-5 max-w-4xl font-display text-5xl leading-[0.95] text-shell md:text-7xl">
              Not a real startup.
              <br />
              Very real data engineering.
            </h1>
            <p className="mt-6 max-w-2xl text-sm leading-7 text-shell/78">
              PulseIQ is what happened when “I should probably learn end-to-end data engineering properly” turned into synthetic source systems, raw Parquet, DuckDB, dbt marts, embeddings, hybrid retrieval, evals, and a chatbot that can actually answer something useful.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => setChatOpen(true)}
                className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-3 text-sm font-semibold text-white transition duration-200 hover:-translate-y-0.5 hover:brightness-95"
              >
                Open chatbot
                <ArrowRight className="h-4 w-4" />
              </button>
              <div className="rounded-full border border-white/10 px-4 py-3 text-sm text-shell/72">
                Built for learning. Shipped like it mattered.
              </div>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {stats.map(({ label, value, icon: Icon }) => (
              <div
                key={label}
                className="rounded-[1.8rem] border border-ink/10 bg-white/85 p-6 shadow-panel backdrop-blur transition duration-200 hover:-translate-y-0.5 hover:border-ink/20"
              >
                <Icon className="h-6 w-6 text-accent" />
                <div className="mt-7 text-[11px] uppercase tracking-[0.24em] text-steel">{label}</div>
                <div className="mt-2 text-2xl font-semibold leading-tight text-ink">{value}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-[2rem] border border-ink/10 bg-white/85 p-8 shadow-panel backdrop-blur">
            <div className="flex items-center gap-3 text-xs uppercase tracking-[0.24em] text-steel">
              <Sparkles className="h-4 w-4 text-accent" />
              Project thesis
            </div>
            <h2 className="mt-3 text-3xl font-semibold text-ink">
              I wanted one serious learning arc, not five half-finished demos.
            </h2>
            <div className="mt-5 space-y-4 text-sm leading-7 text-steel">
              <p>
                So the site is intentionally honest: yes, this is a showcase. No, it is not pretending to be an actual venture-backed company with suspiciously smooth copywriting.
              </p>
              <p>
                The joke is the tone. The non-joke is the backend. The whole point was to understand how ingestion, modeling, serving tables, semantic retrieval, and evaluation fit together in one coherent system.
              </p>
            </div>
          </div>

          <div className="rounded-[2rem] border border-ink/10 bg-mist p-8 shadow-panel">
            <div className="text-xs uppercase tracking-[0.24em] text-pine">Prompt starter pack</div>
            <div className="mt-5 grid gap-3">
              {prompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => handlePromptClick(prompt)}
                  className="rounded-[1.4rem] border border-pine/15 bg-white px-5 py-4 text-left text-sm leading-6 text-ink transition duration-200 hover:-translate-y-0.5 hover:border-pine/30 hover:shadow-panel"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-3">
          {featureCards.map((card) => (
            <div
              key={card.title}
              className="rounded-[2rem] border border-ink/10 bg-white/82 p-7 shadow-panel backdrop-blur transition duration-200 hover:-translate-y-0.5 hover:border-ink/20"
            >
              <div className="text-lg font-semibold text-ink">{card.title}</div>
              <p className="mt-3 text-sm leading-7 text-steel">{card.body}</p>
            </div>
          ))}
        </section>
      </div>

      <div className="fixed bottom-5 right-5 z-30 md:bottom-7 md:right-7">
        {chatOpen ? (
          <div className="w-[calc(100vw-2rem)] max-w-[520px] overflow-hidden rounded-[2rem] border border-ink/10 bg-white/96 shadow-panel backdrop-blur-xl transition duration-200">
            <button
              type="button"
              onClick={() => setChatOpen(false)}
              className="flex w-full items-center justify-between border-b border-ink/10 px-5 py-4 text-left transition duration-200 hover:bg-shell/80"
            >
              <div>
                <div className="text-sm font-semibold text-ink">PulseIQ Assistant</div>
                <div className="text-[11px] uppercase tracking-[0.18em] text-steel">
                  Warehouse marts + semantic retrieval
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="rounded-full bg-ink px-3 py-1 text-[10px] uppercase tracking-[0.16em] text-shell">
                  Live tools
                </div>
                <div className="rounded-full border border-ink/10 p-2 text-steel">
                  <Minus className="h-4 w-4" />
                </div>
              </div>
            </button>

            <div className="max-h-[460px] space-y-3 overflow-y-auto bg-shell/80 p-4">
              {messages.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={`rounded-[1.25rem] px-4 py-3 text-sm leading-6 ${
                    message.role === "user"
                      ? "ml-auto max-w-[85%] bg-ink text-shell"
                      : "max-w-[92%] bg-white text-ink"
                  }`}
                >
                  {message.role === "assistant" ? (
                    <div className="prose prose-sm max-w-none prose-p:my-2 prose-ul:my-2 prose-ul:pl-5 prose-ol:my-2 prose-ol:pl-5 prose-li:my-1 prose-strong:text-ink prose-headings:text-ink prose-code:rounded prose-code:bg-shell prose-code:px-1 prose-code:py-0.5 prose-code:text-[0.9em] prose-pre:bg-ink prose-pre:text-shell">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text}</ReactMarkdown>
                    </div>
                  ) : (
                    <div className="whitespace-pre-wrap">{message.text}</div>
                  )}
                  {message.status ? (
                    <div className="mt-3 inline-flex items-center gap-2 rounded-full bg-shell px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-steel">
                      <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                      {message.status}
                    </div>
                  ) : null}
                  {message.route ? (
                    <div className="mt-2 text-[10px] uppercase tracking-[0.2em] text-steel">
                      Route: {message.route}
                    </div>
                  ) : null}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            <div className="border-t border-ink/10 p-4">
              <div className="flex flex-col gap-3">
                <textarea
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={handleQuestionKeyDown}
                  placeholder="Ask about risk, refunds, complaints, or weird operational patterns..."
                  className="min-h-[88px] w-full resize-none rounded-[1.25rem] border border-ink/10 bg-shell px-4 py-3 text-sm text-ink outline-none placeholder:text-steel/80"
                />
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => void submitQuestion()}
                  className="flex items-center justify-center gap-2 rounded-[1.25rem] bg-accent px-5 py-3 text-sm font-semibold text-white transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Bot className="h-4 w-4" />}
                  {loading ? "Thinking" : "Ask PulseIQ"}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setChatOpen(true)}
            className="group flex items-center gap-3 rounded-full border border-ink/10 bg-white/96 px-5 py-4 shadow-panel backdrop-blur-xl transition duration-200 hover:-translate-y-0.5 hover:border-ink/20"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent text-white">
              <MessageSquare className="h-5 w-5" />
            </div>
            <div className="text-left">
              <div className="text-sm font-semibold text-ink">Open chatbot</div>
              <div className="text-xs text-steel">Ask the warehouse something useful</div>
            </div>
          </button>
        )}
      </div>
    </div>
  );
}
