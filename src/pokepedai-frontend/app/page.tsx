import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100 flex items-center justify-center px-4 py-6">
      <div className="max-w-3xl w-full space-y-10 text-center">
        {/* Logo / Title */}
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 rounded-2xl border border-red-500/40 bg-red-500/10 px-3 py-1 text-xs font-medium text-red-200">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Online • Pokepedai Pokémon Chatbot</span>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl font-semibold tracking-tight text-slate-50">
            Chat with{" "}
            <span className="text-yellow-400">Pokepedai</span>, your Pokémon
            assistant
          </h1>

          <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto">
            Ask about Pokémon stats, moves, types, team building and more.
            Pokepedai mixes Pokédex-style knowledge with a friendly chat
            interface so it feels like talking to your own in-game guide.
          </p>
        </div>

        {/* Primary CTA */}
        <div className="space-y-3">
          <Link
            href="/chat"
            className="inline-flex items-center justify-center gap-2 rounded-2xl bg-red-500 px-6 py-3 text-sm sm:text-base font-semibold text-slate-950 shadow-lg shadow-red-500/30 transition hover:bg-red-400"
          >
            <span>Start a Poké-chat</span>
            <span className="text-lg" aria-hidden>
              ⚡
            </span>
          </Link>

          <p className="text-[0.7rem] sm:text-xs text-slate-500">
            No setup, no login – just open Pokepedai and start asking Pokémon
            questions.
          </p>
        </div>

        {/* Feature highlights */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
            <p className="text-sm font-medium text-slate-100">
              Pokédex-style answers
            </p>
            <p className="text-xs text-slate-400">
              Get clean explanations about abilities, moves, typings, evolutions
              and more in plain language.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
            <p className="text-sm font-medium text-slate-100">
              Pokémon chat icons
            </p>
            <p className="text-xs text-slate-400">
              Give each conversation its own Pokémon avatar so your team
              building, lore and meta chats stay easy to spot.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
            <p className="text-sm font-medium text-slate-100">
              Built for trainers
            </p>
            <p className="text-xs text-slate-400">
              Ask about matchups, movesets or casual questions – Pokepedai keeps
              everything organized per chat.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
