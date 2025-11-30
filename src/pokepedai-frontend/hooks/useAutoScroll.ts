import { RefObject, useEffect } from "react";

/**
 * Hook to enable autoscroll whooo (to go to last message automatically)
 */
export function useAutoScroll<T extends HTMLElement>(
    ref: RefObject<T | null>,
    deps: unknown[]
) {
    useEffect(() => {
        ref.current?.scrollIntoView({ behavior: "smooth" });
    }, deps);
}
