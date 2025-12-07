import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100 flex items-center justify-center px-4 py-6">
      <div className="max-w-3xl w-full space-y-10 text-center">
        {/* Logo / Title */}
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 rounded-2xl border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-200">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Online • Taco Parlicy Chatbot</span>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl font-semibold tracking-tight text-slate-50">
            Chat with your{" "}
            <span className="text-emerald-400">Taco Parlicy</span> assistant
          </h1>

          <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto">
            Ask questions, explore ideas, and keep a history of your
            conversations. Each chat stays organized in the sidebar with its own
            icon, so you can easily jump back into any topic.
          </p>
        </div>

        {/* Primary CTA */}
        <div className="space-y-3">
          <Link
            href="/chat"
            className="inline-flex items-center justify-center gap-2 rounded-2xl bg-emerald-500 px-6 py-3 text-sm sm:text-base font-semibold text-slate-950 shadow-lg shadow-emerald-500/30 transition hover:bg-emerald-400"
          >
            <span>Start chatting</span>
            <span className="text-lg" aria-hidden>
              💬
            </span>
          </Link>

          <p className="text-[0.7rem] sm:text-xs text-slate-500">
            No setup, no login – just open the chat and start typing.
          </p>
        </div>

        {/* Feature highlights */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
            <p className="text-sm font-medium text-slate-100">Multi-chat sidebar</p>
            <p className="text-xs text-slate-400">
              Create multiple sessions for different topics and switch between
              them instantly.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
            <p className="text-sm font-medium text-slate-100">
              Pokémon chat icons
            </p>
            <p className="text-xs text-slate-400">
              Give each conversation its own Pokémon avatar for quick visual
              recognition.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
            <p className="text-sm font-medium text-slate-100">
              Keyboard-friendly
            </p>
            <p className="text-xs text-slate-400">
              Press Enter to send, Shift + Enter for newlines, and stay in the
              flow while you type.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}