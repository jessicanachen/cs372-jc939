"use client";

import { useRef } from "react";
import MessageBubble from "./MessageBubble";
import { useChat } from "@/hooks/useChat";
import { useAutoScroll } from "@/hooks/useAutoScroll";

/**
 * Chat layout with messages and form
 */
export default function ChatLayout() {
    const {
        messages,
        input,
        setInput,
        isLoading,
        handleSubmit,
        handleKeyDown,
    } = useChat();

    const messagesEndRef = useRef<HTMLDivElement | null>(null);
    useAutoScroll(messagesEndRef, [messages, isLoading]);

    return (
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
                {messages.length === 0 && !isLoading && (
                    <MessageBubble
                        role="assistant"
                        content="Hey! I’m your friendly chatbot. Ask me anything to get started 🤖"
                    />
                )}

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
                            maxLength={500}
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
    );
}
