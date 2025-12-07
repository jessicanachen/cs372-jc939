"use client";

import { useMemo, useState } from "react";
import {
  PokemonEntry,
  searchPokemon,
  dexToImageUrl,
} from "@/lib/pokemonIcons";

type ChatIconPickerProps = {
  dexNumber: number | null | undefined;
  name: string | null | undefined;
  onChange: (entry: PokemonEntry | null) => void;
};

export default function ChatIconPicker({
  dexNumber,
  name,
  onChange,
}: ChatIconPickerProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState(name ?? "");

  const suggestions = useMemo(
    () => (open ? searchPokemon(query, 8) : []),
    [query, open]
  );

  const currentLabel =
    name ??
    (dexNumber ? `#${dexNumber.toString().padStart(3, "0")}` : "Choose Pokémon");

  const handleSelect = (entry: PokemonEntry) => {
    onChange(entry);
    setQuery(entry.name);
    setOpen(false);
  };

  const handleClear = () => {
    onChange(null);
    setQuery("");
    setOpen(false);
  };

  return (
    <div className="relative mr-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1 border-[2px] border-black bg-[#f5f3e7] px-1.5 py-0.5 text-[0.6rem] font-bold uppercase tracking-[0.12em]"
      >
        {dexNumber ? (
          <img
            src={dexToImageUrl(dexNumber)}
            alt={currentLabel}
            className="h-6 w-6 border-[2px] border-black bg-[#e7e3d4] object-contain"
          />
        ) : (
          <span className="h-6 w-6 border-[2px] border-black bg-[#e7e3d4] flex items-center justify-center text-[0.6rem]">
            PKMN
          </span>
        )}
      </button>

      {open && (
        <div className="absolute z-20 mt-1 w-52 border-[3px] border-black bg-[#f5f3e7] shadow-[4px_4px_0_rgba(0,0,0,0.75)]">
          <div className="flex items-center gap-1 px-2 py-1 border-b-[2px] border-black">
            <input
              type="text"
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search Pokémon..."
              className="w-full bg-transparent text-[0.7rem] outline-none placeholder:text-neutral-500"
            />
            {dexNumber && (
              <button
                type="button"
                onClick={handleClear}
                className="text-[0.7rem]"
                aria-label="Clear icon"
              >
                ✕
              </button>
            )}
          </div>

          <ul className="max-h-52 overflow-y-auto text-[0.7rem] scrollbar-thin scrollbar-thumb-neutral-500 scrollbar-track-transparent">
            {suggestions.length === 0 && (
              <li className="px-3 py-2 text-neutral-600">No matches</li>
            )}

            {suggestions.map((p) => (
              <li key={p.dex}>
                <button
                  type="button"
                  onClick={() => handleSelect(p)}
                  className="flex w-full items-center gap-2 px-3 py-1.5 hover:bg-[#e4e0d0] text-left"
                >
                  <img
                    src={dexToImageUrl(p.dex)}
                    alt={p.name}
                    className="h-6 w-6 border-[2px] border-black bg-[#e7e3d4] object-contain"
                  />
                  <span className="capitalize">{p.name}</span>
                  <span className="ml-auto text-[0.65rem] text-neutral-600">
                    #{p.dex.toString().padStart(3, "0")}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
