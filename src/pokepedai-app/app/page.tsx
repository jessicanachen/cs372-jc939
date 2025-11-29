"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

type Role = "user" | "assistant";

type Message = {
  id: number;
  role: Role;
  content: string;
};

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: "assistant",
      content: "Hey! I’m your friendly chatbot. Ask me anything to get started 🤖",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const userMessage: Message = {
      id: Date.now(),
      role: "user",
      content: trimmed,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // TODO: Replace this fake reply with a real API call to your backend.
      // Example:
      //
      // const res = await fetch("/api/chat", {
      //   method: "POST",
      //   headers: { "Content-Type": "application/json" },
      //   body: JSON.stringify({ message: trimmed }),
      // });
      // const data = await res.json();
      // const assistantText = data.reply;

      const assistantText = await fakeAssistantReply(trimmed);

      const assistantMessage: Message = {
        id: Date.now() + 1,
        role: "assistant",
        content: assistantText,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage: Message = {
        id: Date.now() + 2,
        role: "assistant",
        content:
          "Oops, something went wrong while generating a response. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      // Manually submit the form
      const form = e.currentTarget.form;
      if (form) {
        form.requestSubmit();
      }
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100 flex items-center justify-center px-4 py-6">
      <div className="w-full max-w-3xl h-[80vh] flex flex-col rounded-3xl border border-slate-800 bg-slate-900/70 shadow-2xl backdrop-blur">
        {/* Header */}
        <header className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-2xl bg-slate-800 flex items-center justify-center text-xl">
              🤖
            </div>
            <div>
              <h1 className="text-sm font-semibold text-slate-50">
                Taco Parlicy Chatbot
              </h1>
              <p className="text-xs text-slate-400 flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                Online • ready to chat
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="hidden sm:inline">Press</span>
            <kbd className="rounded-md border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-[0.65rem] font-medium">
              Enter
            </kbd>
            <span className="hidden sm:inline">to send</span>
            <span className="hidden sm:inline">•</span>
            <span className="hidden sm:inline">Shift + Enter = newline</span>
          </div>
        </header>

        {/* Messages */}
        <section className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
          {messages.map((m) => (
            <MessageBubble key={m.id} role={m.role} content={m.content} />
          ))}
          {isLoading && (
            <div className="flex gap-2 items-center text-xs text-slate-400 px-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-bounce" />
              Thinking…
            </div>
          )}
          <div ref={messagesEndRef} />
        </section>

        {/* Input */}
        <footer className="border-t border-slate-800 px-4 py-3">
          <form
            onSubmit={handleSubmit}
            className="flex flex-col gap-2 sm:flex-row sm:items-end"
          >
            <div className="relative flex-1">
              <textarea
                className="block w-full resize-none rounded-2xl border border-slate-700 bg-slate-900/80 px-3 py-2 pr-12 text-sm text-slate-50 shadow-sm outline-none placeholder:text-slate-500 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/50"
                rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question or say hi..."
              />
              <span className="pointer-events-none absolute bottom-2.5 right-3 text-[0.65rem] text-slate-500">
                {input.length}/500
              </span>
            </div>

            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="inline-flex items-center justify-center rounded-2xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 shadow-lg shadow-emerald-500/30 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-300 disabled:shadow-none"
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <span className="h-3 w-3 animate-spin rounded-full border-[2px] border-slate-900 border-t-transparent" />
                  Sending…
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <span>Send</span>
                  <span className="text-xs">↵</span>
                </span>
              )}
            </button>
          </form>
        </footer>
      </div>
    </main>
  );
}

// Simple fake assistant reply for now.
// Replace this with your actual model / API call.
async function fakeAssistantReply(userMessage: string): Promise<string> {
  await new Promise((resolve) => setTimeout(resolve, 600)); // mimic latency
  return `You said: “${userMessage}”\n\nThis is a placeholder response. Wire me up to your real /api/chat endpoint to get model answers.`;
}

type MessageBubbleProps = {
  role: Role;
  content: string;
};

function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div
      className={`flex w-full ${
        isUser ? "justify-end" : "justify-start"
      } text-sm`}
    >
      <div
        className={`max-w-[80%] rounded-2xl px-3 py-2 shadow-sm ${
          isUser
            ? "bg-emerald-500 text-slate-950 rounded-br-sm"
            : "bg-slate-800 text-slate-50 rounded-bl-sm"
        }`}
      >
        {!isUser && (
          <p className="mb-1 text-[0.65rem] font-semibold uppercase tracking-wide text-emerald-300">
            Assistant
          </p>
        )}
        <p className="whitespace-pre-wrap leading-relaxed">{content}</p>
      </div>
    </div>
  );
}
