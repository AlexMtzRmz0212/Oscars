import type { ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";
import { useSearch } from "../search/SearchContext";
import "./SiteBar.css";

const LINKS = [
  ["/season", "The 99th"],
  ["/ceremonies", "Ceremonies"],
  ["/categories", "Categories"],
  ["/methods", "Methods"],
];

export function SiteBar({ action }: { action?: ReactNode }) {
  const { openSearch } = useSearch();

  return (
    <header className="site-bar">
      <Link className="site-wordmark" to="/" translate="no">
        Every Envelope
      </Link>
      <nav className="site-links" aria-label="Main">
        {LINKS.map(([to, label]) => (
          <NavLink key={to} to={to}>
            {label}
          </NavLink>
        ))}
        <button type="button" className="site-search" onClick={openSearch}>
          Search
        </button>
      </nav>
      {action}
    </header>
  );
}
