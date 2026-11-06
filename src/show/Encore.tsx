import { motion } from "motion/react";
import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { findYearEntry, YearCard, yearRange } from "../components/YearCard";
import { bornHref } from "../lib/archive";
import { rise } from "../lib/motion";
import type { EncoreEntry } from "../lib/types";
import { useStoryData } from "../lib/useStoryData";
import { useSearch } from "../search/SearchContext";
import "./Encore.css";

export function Encore() {
  const story = useStoryData<EncoreEntry[]>("encore");
  const { openSearch } = useSearch();
  const [input, setInput] = useState("");
  const [opened, setOpened] = useState<{ entry: EncoreEntry; year: number } | null>(null);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (story.status !== "ready") return;
    const year = Number(input);
    const entry = input.trim() && Number.isInteger(year) ? findYearEntry(story.data, year) : undefined;
    const { first, last } = yearRange(story.data);
    setOpened(entry ? { entry, year } : null);
    setError(entry ? "" : `Enter a year from ${first} to ${last}.`);
    if (!entry) inputRef.current?.focus();
  }

  return (
    <section className="encore" id="encore" aria-labelledby="encore-title">
      <motion.h2 id="encore-title" {...rise}>
        Encore: your envelope
      </motion.h2>
      <motion.p className="encore-lead" {...rise}>
        Every year has one. Enter the year you were born, or any year, and open it.
      </motion.p>

      <form className="encore-form" onSubmit={handleSubmit} noValidate>
        <label htmlFor="encore-year">Year</label>
        <input
          id="encore-year"
          ref={inputRef}
          name="year"
          type="text"
          inputMode="numeric"
          autoComplete="off"
          maxLength={4}
          placeholder="1997…"
          value={input}
          aria-describedby={error ? "encore-error" : undefined}
          aria-invalid={Boolean(error)}
          onChange={(event) => setInput(event.target.value)}
        />
        <button className="button" type="submit" disabled={story.status !== "ready"}>
          Open the envelope
        </button>
        <button className="encore-search" type="button" onClick={openSearch}>
          Or search every film and person
        </button>
      </form>
      {error && (
        <p className="encore-error" id="encore-error" role="alert">
          {error}
        </p>
      )}
      {story.status === "error" && (
        <p className="encore-error" role="alert">
          The envelopes didn’t load. Refresh the page to try again.
        </p>
      )}
      <div aria-live="polite">
        {opened && (
          <>
            <YearCard entry={opened.entry} />
            <p className="encore-share">
              <Link to={bornHref(opened.year)}>A page of its own for {opened.year}</Link>
            </p>
          </>
        )}
      </div>
    </section>
  );
}
