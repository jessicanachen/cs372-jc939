"use client";

import {
    FormEvent,
    KeyboardEvent,
    useCallback,
    useState,
} from "react";
import type { Message } from "@/types/chat";
import { buildHistoryPayload } from "@/lib/history";
import { chatClient } from "@/lib/chatClient";

/**
 * All chatlogic, state, and error handling
 */
export function useChat() {
    const [messages, setMessages] = useState<Message[]>([]);    // message history
    const [input, setInput] = useState("");                     // user input
    const [isLoading, setIsLoading] = useState(false);          // is reply loading

    // handling sending message
    const handleSubmit = useCallback(
        // this is the input
        async (e: FormEvent<HTMLFormElement>) => {
            e.preventDefault();
            const trimmed = input.trim();

            if (!trimmed || isLoading) return;

            const userMessage: Message = {
                id: Date.now(),
                role: "user",
                content: trimmed,
            };

            // add user message to messages, clear input, loading backend response
            setMessages((prev) => [...prev, userMessage]);
            setInput("");
            setIsLoading(true);

            // try backending
            try {
                // generate the past history
                const historyForApi = buildHistoryPayload(messages);

                // try to send the message
                const result = await chatClient.sendMessage(
                    historyForApi,
                    trimmed,
                );

                let assistantText: string;

                // get what should be displayed (error or reply)
                if (!result.ok) {
                    assistantText = chatClient.getErrorMessage(result);
                } else {
                    assistantText = chatClient.getReplyMessage(result);
                }

                // add the message
                const assistantMessage: Message = {
                    id: Date.now() + 1,
                    role: "assistant",
                    content: assistantText,
                };

                setMessages((prev) => [...prev, assistantMessage]);
            } catch (err: unknown) {
                // errors should be logged
                console.error(err);

                // general error message for unknown
                let friendlyMessage =
                    "Oops, something went wrong while generating a response. Please try again.";

                // timeout, or no server
                if ((err as any).name === "AbortError") {
                    friendlyMessage =
                        "Hmm, the server is taking too long to respond. Please try again in a moment.";
                } else if (err instanceof TypeError && err.message === "Failed to fetch") {
                    friendlyMessage =
                        "I couldn't reach the server. Please check your connection and try again.";
                } else if (err instanceof Error && err.message) {
                    friendlyMessage = err.message;
                }

                const errorMessage: Message = {
                    id: Date.now() + 2,
                    role: "assistant",
                    content: friendlyMessage,
                };

                setMessages((prev) => [...prev, errorMessage]);
            } finally {
                setIsLoading(false);
            }
        },
        [input, isLoading, messages]
    );

    // enter also submits this
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

    return {
        messages,
        input,
        setInput,
        isLoading,
        handleSubmit,
        handleKeyDown,
    };
}
