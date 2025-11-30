"use client";

import { useRef } from "react";
import MessageBubble from "./MessageBubble";
import ChatSidebar from "./ChatSidebar";
import { useChatSessions } from "@/hooks/useChatSessions";
import { useAutoScroll } from "@/hooks/useAutoScroll";

export default function ChatLayout() {
    const {
        initialized,
        sessions,
        activeSession,
        activeSessionId,
        input,
        setInput,
        isLoading,
        handleSubmit,
        handleKeyDown,
        createNewSession,
        selectSession,
        clearActiveSession,
        deleteSession,
        updateSessionIcon,
    } = useChatSessions();

    const messagesEndRef = useRef<HTMLDivElement | null>(null);
    useAutoScroll(messagesEndRef, [activeSession?.messages, isLoading]);

    const messages = activeSession?.messages ?? [];

    return (
        <div className="w-full max-w-4xl h-[80vh] flex rounded-3xl border border-slate-800 bg-slate-900/70 shadow-2xl backdrop-blur overflow-hidden">
            {/* Sidebar with chat list */}
            <ChatSidebar
                sessions={sessions}
                activeSessionId={activeSessionId}
                onSelectSession={selectSession}
                onNewSession={createNewSession}
                onDeleteSession={deleteSession}
                onChangeIcon={updateSessionIcon}
            />

            {/* Main chat column */}
            <div className="flex flex-1 flex-col min-w-0">
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

                    <div className="flex items-center gap-3 text-xs text-slate-400">
                        <div className="hidden sm:flex items-center gap-2">
                            <span>Press</span>
                            <kbd className="rounded-md border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-[0.65rem] font-medium">
                                Enter
                            </kbd>
                            <span>to send</span>
                            <span>•</span>
                            <span>Shift + Enter = newline</span>
                        </div>

                        <button
                            type="button"
                            onClick={clearActiveSession}
                            disabled={!initialized || !activeSession}
                            className="inline-flex items-center rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-[0.7rem] font-medium text-slate-200 hover:border-red-500 hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Clear chat
                        </button>
                    </div>
                </header>

                {/* Messages */}
                <section className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
                    {/* One-time greeting when current session is empty */}
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
                                disabled={!initialized}
                            />
                            <span className="pointer-events-none absolute bottom-2.5 right-3 text-[0.65rem] text-slate-500">
                                {input.length}/500
                            </span>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading || !input.trim() || !initialized}
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
        </div>
    );
}
