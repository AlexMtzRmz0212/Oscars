import { createContext, lazy, Suspense, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

const SearchDialog = lazy(() => import("./SearchDialog"));

interface SearchContextValue {
  openSearch: () => void;
}

const SearchContext = createContext<SearchContextValue>({ openSearch: () => {} });

export const useSearch = () => useContext(SearchContext);

const isTyping = (target: EventTarget | null) =>
  target instanceof HTMLElement && (target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName));

/** The search code and its index load only when search is first opened. */
export function SearchProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const openSearch = useCallback(() => {
    setLoaded(true);
    setOpen(true);
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey && !isTyping(event.target)) {
        event.preventDefault();
        openSearch();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [openSearch]);

  const value = useMemo(() => ({ openSearch }), [openSearch]);

  return (
    <SearchContext.Provider value={value}>
      {children}
      {loaded && (
        <Suspense fallback={null}>
          <SearchDialog open={open} onClose={() => setOpen(false)} />
        </Suspense>
      )}
    </SearchContext.Provider>
  );
}
