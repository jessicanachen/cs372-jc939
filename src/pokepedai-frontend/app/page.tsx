import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#b8b3a0] flex items-center justify-center px-4 py-6">
      <div className="max-w-3xl w-full border-[6px] border-black bg-[#f5f3e7] text-[#111111] shadow-[8px_8px_0_rgba(0,0,0,0.75)] p-6 font-mono">
        <header className="border-b-[3px] border-black pb-3 mb-4 text-center">
          <p className="text-[0.8rem] uppercase tracking-[0.25em]">
            POKEPEDAI BATTLE SCREEN
          </p>
          <p className="mt-1 text-[0.65rem]">
            Press START to begin your adventure.
          </p>
        </header>

        <div className="text-center mb-6">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold tracking-tight mb-2">
            Pokepedai – Pokémon Chat
          </h1>
          <p className="text-[0.8rem] sm:text-sm max-w-2xl mx-auto">
            Ask about Pokémon stats, moves, types, evolutions and strategies.
            Pokepedai answers in a Pokédex-style chat, just like an old
            handheld battle screen.
          </p>
        </div>

        <div className="flex flex-col items-center gap-3 mb-6">
          <Link
            href="/chat"
            className="inline-flex items-center justify-center gap-2 border-[3px] border-black bg-[#e7e3d4] px-6 py-3 text-sm sm:text-base font-bold uppercase tracking-[0.18em] shadow-[4px_4px_0_rgba(0,0,0,0.8)] active:translate-x-[1px] active:translate-y-[1px] active:shadow-none"
          >
            Start
          </Link>
          <p className="text-[0.65rem]">
            A = Select&nbsp;&nbsp;•&nbsp;&nbsp;B = Back
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-[0.75rem]">
          <div className="border-[3px] border-black bg-[#f0ecde] p-3">
            <p className="font-bold mb-1">Pokédex answers</p>
            <p>
              Learn about abilities, typings, evolutions and more with clean,
              in-world explanations.
            </p>
          </div>

          <div className="border-[3px] border-black bg-[#f0ecde] p-3">
            <p className="font-bold mb-1">Chat icons</p>
            <p>
              Give each chat its own Pokémon portrait, like naming your party
              slots.
            </p>
          </div>

          <div className="border-[3px] border-black bg-[#f0ecde] p-3">
            <p className="font-bold mb-1">Trainer friendly</p>
            <p>
              Talk about matchups, movesets or casual lore – one save file per
              conversation.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
