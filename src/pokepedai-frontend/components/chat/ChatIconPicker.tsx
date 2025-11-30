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
                className="flex items-center gap-1 rounded-full border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-[0.65rem] text-slate-200 hover:border-emerald-500"
            >
                {dexNumber ? (
                    <img
                        src={dexToImageUrl(dexNumber)}
                        alt={currentLabel}
                        className="h-6 w-6 rounded-full bg-slate-800 object-contain"
                    />
                ) : (
                    <span className="h-6 w-6 rounded-full bg-slate-800 flex items-center justify-center">
                        🎴
                    </span>
                )}
            </button>

            {open && (
                <div className="absolute z-20 mt-1 w-48 rounded-xl border border-slate-700 bg-slate-950 shadow-lg">
                    <div className="flex items-center gap-1 px-2 py-1 border-b border-slate-800">
                        <input
                            type="text"
                            autoFocus
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search Pokémon..."
                            className="w-full bg-transparent text-[0.7rem] text-slate-100 outline-none placeholder:text-slate-500"
                        />
                        {dexNumber && (
                            <button
                                type="button"
                                onClick={handleClear}
                                className="text-[0.7rem] text-slate-500 hover:text-red-400 px-1"
                                aria-label="Clear icon"
                            >
                                ✕
                            </button>
                        )}
                    </div>

                    <ul className="max-h-52 overflow-y-auto text-[0.7rem]">
                        {suggestions.length === 0 && (
                            <li className="px-3 py-2 text-slate-500">No matches</li>
                        )}

                        {suggestions.map((p) => (
                            <li key={p.dex}>
                                <button
                                    type="button"
                                    onClick={() => handleSelect(p)}
                                    className="flex w-full items-center gap-2 px-3 py-1.5 hover:bg-slate-800 text-left"
                                >
                                    <img
                                        src={dexToImageUrl(p.dex)}
                                        alt={p.name}
                                        className="h-6 w-6 rounded-full bg-slate-800 object-contain"
                                    />
                                    <span className="capitalize text-slate-100">
                                        {p.name}
                                    </span>
                                    <span className="ml-auto text-[0.65rem] text-slate-500">
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
