"use client";

import type { ChatSession } from "@/types/chat";
import type { PokemonEntry } from "@/lib/pokemonIcons";
import ChatIconPicker from "./ChatIconPicker";

type ChatSidebarProps = {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: (id: string) => void;
  onChangeIcon: (sessionId: string, entry: PokemonEntry | null) => void;
  isOpen: boolean;
  onClose: () => void;
};

export default function ChatSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onChangeIcon,
  isOpen,
  onClose,
}: ChatSidebarProps) {
  return (
    <aside
      className={`flex flex-col w-64 border-r-[4px] border-black bg-[#f5f3e7] text-[#111111]
                transform transition-transform duration-200 ease-out
                fixed inset-y-0 left-0 z-30 max-w-[80vw]
                ${isOpen ? "translate-x-0" : "-translate-x-full"}`}
    >
      <div className="flex items-center justify-between px-4 py-3 border-b-[3px] border-black bg-[#e7e3d4]">
        <h2 className="text-[0.7rem] font-bold uppercase tracking-[0.18em]">
          Pokepedai Chats
        </h2>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onNewSession}
            className="border-[2px] border-black bg-[#f5f3e7] px-2 py-1 text-[0.6rem] font-bold uppercase tracking-[0.15em] shadow-[2px_2px_0_rgba(0,0,0,0.8)] active:translate-x-[1px] active:translate-y-[1px] active:shadow-none"
          >
            New
          </button>
          <button
            type="button"
            onClick={onClose}
            className="text-[0.8rem]"
            aria-label="Close chat list"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1 scrollbar-thin scrollbar-thumb-neutral-500 scrollbar-track-transparent">
        {sessions.map((session) => {
          const isActive = session.id === activeSessionId;
          const lastMessage =
            session.messages[session.messages.length - 1]?.content ?? "";
          const previewSource =
            session.title !== "New chat" ? session.title : lastMessage || "New chat";

          const preview =
            previewSource.length > 40
              ? previewSource.slice(0, 37) + "…"
              : previewSource;

          return (
            <div
              key={session.id}
              role="button"
              tabIndex={0}
              onClick={() => {
                onSelectSession(session.id);
                onClose();
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelectSession(session.id);
                  onClose();
                }
              }}
              className={`group flex w-full items-center justify-between px-2.5 py-2 text-left text-[0.7rem] cursor-pointer border-[2px] border-black ${
                isActive
                  ? "bg-[#d8d4c4]"
                  : "bg-[#f5f3e7] hover:bg-[#e4e0d0]"
              }`}
            >
              <div className="flex items-center gap-2 mr-2 w-[80%]">
                <ChatIconPicker
                  dexNumber={session.iconDexNumber ?? null}
                  name={session.iconName ?? null}
                  onChange={(entry) => onChangeIcon(session.id, entry)}
                />
                <div className="flex-1 min-w-0">
                  <p className="font-semibold truncate">{preview}</p>
                  <p className="text-[0.6rem] text-neutral-600 truncate">
                    {new Date(session.updatedAt).toLocaleString(undefined, {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(session.id);
                }}
                className="shrink-0 text-[0.65rem] opacity-0 group-hover:opacity-100 hover:text-red-600 px-1"
                aria-label="Delete chat"
              >
                ✕
              </button>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
