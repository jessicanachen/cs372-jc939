"use client";

import { useRef, useState } from "react";
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

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const toggleSidebar = () => setIsSidebarOpen((prev) => !prev);
  const closeSidebar = () => setIsSidebarOpen(false);

  return (
    <div className="relative mx-auto flex h-full min-h-screen w-full flex-col font-mono text-[#111111] bg-[#e7e3d4] border-[6px] border-black shadow-[8px_8px_0_rgba(0,0,0,0.75)] overflow-hidden">
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/40"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      <ChatSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={(id) => {
          selectSession(id);
          closeSidebar();
        }}
        onNewSession={() => {
          createNewSession();
          closeSidebar();
        }}
        onDeleteSession={deleteSession}
        onChangeIcon={updateSessionIcon}
        isOpen={isSidebarOpen}
        onClose={closeSidebar}
      />

      {/* Top “battle screen” title bar */}
      <header className="flex items-center justify-between border-b-[3px] border-black bg-[#f0ecde] px-4 py-2 text-[0.7rem] uppercase tracking-[0.25em]">
        <button
          type="button"
          onClick={toggleSidebar}
          className="border-[2px] border-black bg-[#e7e3d4] px-2 py-1 text-[0.6rem] font-bold shadow-[2px_2px_0_rgba(0,0,0,0.8)] active:translate-x-[1px] active:translate-y-[1px] active:shadow-none"
          aria-label="Toggle chat list"
        >
          Menu
        </button>

        <div className="flex flex-col items-center leading-none">
          <span className="text-xs font-bold tracking-[0.25em]">
            POKEPEDAI BATTLE SCREEN
          </span>
          <span className="mt-1 text-[0.6rem] normal-case tracking-normal">
            What will you ask?
          </span>
        </div>

        <button
          type="button"
          onClick={clearActiveSession}
          disabled={!initialized || !activeSession}
          className="border-[2px] border-black bg-[#e7e3d4] px-2 py-1 text-[0.6rem] font-bold uppercase tracking-[0.15em] shadow-[2px_2px_0_rgba(0,0,0,0.8)] active:translate-x-[1px] active:translate-y-[1px] active:shadow-none disabled:opacity-50 disabled:shadow-none disabled:translate-x-0 disabled:translate-y-0"
        >
          Clear
        </button>
      </header>

      {/* Middle: big battle text box */}
      <section className="flex-1 min-h-0 px-3 py-3">
        <div className="h-full w-full border-[3px] border-black bg-[#f5f3e7] p-2 overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-neutral-500 scrollbar-track-transparent">
          {messages.length === 0 && !isLoading && (
            <MessageBubble
              role="assistant"
              content={"POKEPEDAI appeared!\nWhat will you ask?"}
            />
          )}

          {messages.map((m) => (
            <MessageBubble key={m.id} role={m.role} content={m.content} />
          ))}

          {isLoading && (
            <div className="text-[0.7rem] leading-snug">
              <span className="font-bold">POKEPEDAI:</span> Thinking…
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </section>

      {/* Bottom: command box with input */}
      <footer className="px-3 pb-3">
        <div className="w-full border-[3px] border-black bg-[#f5f3e7] p-2">
          <form
            onSubmit={handleSubmit}
            className="flex flex-col gap-2 sm:flex-row sm:items-end"
          >
            <div className="relative flex-1">
              <textarea
                className="block w-full resize-none bg-transparent text-[0.75rem] leading-snug outline-none pr-10"
                rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="FIGHT / ITEM / POKéMON / RUN ... (type your question)"
                maxLength={500}
                disabled={!initialized}
              />
              <span className="pointer-events-none absolute bottom-0 right-0 text-[0.6rem] text-neutral-500">
                {input.length}/500
              </span>
            </div>

            <button
              type="submit"
              disabled={isLoading || !input.trim() || !initialized}
              className="mt-1 inline-flex items-center justify-center border-[2px] border-black bg-[#e7e3d4] px-4 py-2 text-[0.7rem] font-bold uppercase tracking-[0.15em] shadow-[3px_3px_0_rgba(0,0,0,0.8)] active:translate-x-[1px] active:translate-y-[1px] active:shadow-none disabled:opacity-60 disabled:shadow-none disabled:translate-x-0 disabled:translate-y-0"
            >
              {isLoading ? "Sending…" : "Send"}
            </button>
          </form>

          <p className="mt-1 text-[0.55rem] uppercase tracking-[0.18em] text-neutral-600">
            A = Send&nbsp;&nbsp;•&nbsp;&nbsp;B = New line
          </p>
        </div>
      </footer>
    </div>
  );
}
