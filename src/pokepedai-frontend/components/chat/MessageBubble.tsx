import type { Role } from "@/types/chat";

type MessageBubbleProps = {
  role: Role;
  content: string;
};

/**
 * Single message line in a GB-style text box.
 */
export default function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div
      className={`w-full text-[0.75rem] leading-snug ${
        isUser ? "text-right" : "text-left"
      }`}
    >
      <p className="whitespace-pre-wrap">
        <span className="font-bold">
          {isUser ? "YOU: " : "POKEPEDAI: "}
        </span>
        {content}
      </p>
    </div>
  );
}
