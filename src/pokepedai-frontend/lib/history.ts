import type { Message } from "@/types/chat";

const MAX_HISTORY_MESSAGES = 8;
const MAX_HISTORY_CHARS = 3200;

/**
 * Trim history to MAX_HISTORY_MESSAGES most recent messages
 */
function trimHistory(messages: Message[]): Message[] {
    const trimmed: Message[] = [];
    let totalChars = 0;

    // keep most recent
    for (let i = messages.length - 1; i >= 0; i--) {
        const msg = messages[i];
        const length = msg.content.length;

        if (
            trimmed.length >= MAX_HISTORY_MESSAGES ||
            totalChars + length > MAX_HISTORY_CHARS
        ) {
            break;
        }

        trimmed.unshift(msg);
        totalChars += length;
    }

    return trimmed;
}

export type HistoryPayloadItem = {
    role: "user" | "assistant";
    message: string;
};

/**
 * Converts message history into the payload backend expects.
 */
export function buildHistoryPayload(messages: Message[]): HistoryPayloadItem[] {
    const trimmed = trimHistory(messages);
    return trimmed.map((m) => ({
        role: m.role,
        message: m.content,
    }));
}
