import type { Role } from "@/types/chat";

type MessageBubbleProps = {
    role: Role;
    content: string;
};

/**
 * One message, user or assistant.
 */
export default function MessageBubble({ role, content }: MessageBubbleProps) {
    const isUser = role === "user";

    return (
        <div
            className={`flex w-full ${isUser ? "justify-end" : "justify-start"
                } text-sm`}
        >
            <div
                className={`max-w-[80%] rounded-2xl px-3 py-2 shadow-sm ${isUser
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
