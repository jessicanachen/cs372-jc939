"use client";

import {
    FormEvent,
    KeyboardEvent,
    useCallback,
    useEffect,
    useMemo,
    useState,
} from "react";
import type { ChatSession, Message } from "@/types/chat";
import { buildHistoryPayload } from "@/lib/history";
import { chatClient } from "@/lib/chatClient";

const STORAGE_KEY = "pokepedia-chat-sessions-v1";

/**
 * Create a new session
 */
function createEmptySession(): ChatSession {
    const now = new Date().toISOString();
    return {
        id: `session-${now}-${Math.random().toString(36).slice(2, 10)}`,
        title: "New chat",
        messages: [],
        createdAt: now,
        updatedAt: now,
    };
}

export function useChatSessions() {
    // session information
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    
    // stuff per chat 
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [initialized, setInitialized] = useState(false);

    // initial load from localStorage
    useEffect(() => {
        if (typeof window === "undefined") return;

        try {
            const raw = window.localStorage.getItem(STORAGE_KEY);
            if (raw) {
                const parsed = JSON.parse(raw) as {
                    sessions?: ChatSession[];
                    activeSessionId?: string | null;
                };
                if (parsed.sessions && parsed.sessions.length > 0) {
                    setSessions(parsed.sessions);
                    const fallbackId = parsed.sessions[0].id;
                    const activeId =
                        parsed.activeSessionId &&
                            parsed.sessions.some((s) => s.id === parsed.activeSessionId)
                            ? parsed.activeSessionId
                            : fallbackId;
                    setActiveSessionId(activeId);
                    setInitialized(true);
                    return;
                }
            }
        } catch (err) {
            console.error("Failed to load chat sessions from storage", err);
        }

        // if nothing in storage, create the first session
        const initial = createEmptySession();
        setSessions([initial]);
        setActiveSessionId(initial.id);
        setInitialized(true);
    }, []);

    // persists chat to local storage
    useEffect(() => {
        if (!initialized || typeof window === "undefined") return;
        try {
            const payload = JSON.stringify({ sessions, activeSessionId });
            window.localStorage.setItem(STORAGE_KEY, payload);
        } catch (err) {
            console.error("Failed to save chat sessions to storage", err);
        }
    }, [sessions, activeSessionId, initialized]);

    const activeSession = useMemo(
        () => sessions.find((s) => s.id === activeSessionId) ?? null,
        [sessions, activeSessionId]
    );

    // handle user input (want to chat)
    const handleSubmit = useCallback(
        async (e: FormEvent<HTMLFormElement>) => {
            e.preventDefault();
            if (!initialized || !activeSessionId) return;

            const trimmed = input.trim();
            if (!trimmed || isLoading) return;

            const userMessage: Message = {
                id: Date.now(),
                role: "user",
                content: trimmed,
            };

            // figure out which session it is, build payload based on that
            const sessionSnapshot = sessions.find((s) => s.id === activeSessionId);
            if (!sessionSnapshot) return;

            const historyForApi = buildHistoryPayload(sessionSnapshot.messages);

            // add user input to that session
            setSessions((prev) =>
                prev.map((s) =>
                    s.id === activeSessionId
                        ? {
                            ...s,
                            messages: [...s.messages, userMessage],
                            title:
                                s.title === "New chat" && s.messages.length === 0
                                    ? trimmed.slice(0, 30) || "New chat"
                                    : s.title,
                            updatedAt: new Date().toISOString(),
                        }
                        : s
                )
            );

            setInput("");
            setIsLoading(true);

            // try to get backend
            try {
                const result = await chatClient.sendMessage(historyForApi, trimmed);

                const assistantText = result.ok
                    ? chatClient.getReplyMessage(result)
                    : chatClient.getErrorMessage(result);

                const assistantMessage: Message = {
                    id: Date.now() + 1,
                    role: "assistant",
                    content: assistantText,
                };

                setSessions((prev) =>
                    prev.map((s) =>
                        s.id === activeSessionId
                            ? {
                                ...s,
                                messages: [...s.messages, assistantMessage],
                                updatedAt: new Date().toISOString(),
                            }
                            : s
                    )
                );
            } catch (err: unknown) {
                console.error(err);

                let friendlyMessage =
                    "Oops, something went wrong while generating a response. Please try again.";

                if ((err as any).name === "AbortError") {
                    friendlyMessage =
                        "Hmm, the server is taking too long to respond. Please try again in a moment.";
                } else if (err instanceof TypeError && err.message === "Failed to fetch") {
                    friendlyMessage =
                        "I couldn’t reach the server. Please check your connection and try again.";
                } else if (err instanceof Error && err.message) {
                    friendlyMessage = err.message;
                }

                const errorMessage: Message = {
                    id: Date.now() + 2,
                    role: "assistant",
                    content: friendlyMessage,
                };

                setSessions((prev) =>
                    prev.map((s) =>
                        s.id === activeSessionId
                            ? {
                                ...s,
                                messages: [...s.messages, errorMessage],
                                updatedAt: new Date().toISOString(),
                            }
                            : s
                    )
                );
            } finally {
                setIsLoading(false);
            }
        },
        [input, isLoading, activeSessionId, initialized, sessions]
    );

    const handleKeyDown = useCallback(
        (e: KeyboardEvent<HTMLTextAreaElement>) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                const form = e.currentTarget.form;
                if (form) {
                    form.requestSubmit();
                }
            }
        },
        []
    );

    // methods for creating, clearing, selecting, deleting sessions
    const createNewSession = useCallback(() => {
        const newSession = createEmptySession();
        setSessions((prev) => [newSession, ...prev]);
        setActiveSessionId(newSession.id);
        setInput("");
    }, []);

    const selectSession = useCallback((id: string) => {
        setActiveSessionId(id);
        setInput("");
    }, []);

    const clearActiveSession = useCallback(() => {
        if (!activeSessionId) return;
        setSessions((prev) =>
            prev.map((s) =>
                s.id === activeSessionId
                    ? {
                        ...s,
                        messages: [],
                        updatedAt: new Date().toISOString(),
                    }
                    : s
            )
        );
    }, [activeSessionId]);

    const deleteSession = useCallback(
        (id: string) => {
            setSessions((prev) => {
                const filtered = prev.filter((s) => s.id !== id);

                if (filtered.length === 0) {
                    const fresh = createEmptySession();
                    setActiveSessionId(fresh.id);
                    return [fresh];
                }

                if (id === activeSessionId) {
                    setActiveSessionId(filtered[0].id);
                }

                return filtered;
            });
        },
        [activeSessionId]
    );

    return {
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
    };
}
