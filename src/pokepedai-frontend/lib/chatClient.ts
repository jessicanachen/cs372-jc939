import { API_BASE_URL } from "./config";
import type { HistoryPayloadItem } from "./history";

export type ChatResponseBody = {
    reply?: string;
    error?: string;
    detail?: string;
    message?: string;
};

export type ChatClientResult = {
    ok: boolean;
    status: number;
    data: ChatResponseBody;
};

/**
 * Class to handle chat api and errors.
 */
export class ChatClient {
    constructor(private readonly baseUrl: string = API_BASE_URL) { }

    /**
     * Sends message to backend
     */
    async sendMessage(
        history: HistoryPayloadItem[],
        message: string,
        timeoutMs: number = 300000
    ): Promise<ChatClientResult> {
        // timeout
        const controller = new AbortController();
        const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

        // send message
        try {
            const res = await fetch(`${this.baseUrl}/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ history, message }),
                signal: controller.signal,
            });

            let data: ChatResponseBody = {};
            try {
                data = (await res.json()) ?? {};
            } catch {
                // purposely blank, keeps data as {}
            }

            return {
                ok: res.ok,
                status: res.status,
                data,
            };
        } finally {
            window.clearTimeout(timeoutId);
        }
    }

    /**
     * Get backend error
     */
    getErrorMessage(result: ChatClientResult): string {
        const { data, status } = result;

        return (
            data.error ||
            data.detail ||
            data.message ||
            (status >= 500
                ? "The server had an internal error. Please try again in a moment."
                : "I couldn't process that request. Please try again.")
        );
    }

    /**
     * Get backend reply
     */
    getReplyMessage(result: ChatClientResult): string {
        const raw = (result.data.reply ?? "").trim();
        return raw || "Sorry, I didn't get a response.";
    }
}

// makes one chatClient for each instance
export const chatClient = new ChatClient();
