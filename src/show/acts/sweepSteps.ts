import type { FilmSummary, SweepCell, SweepData } from "../../lib/types";
import { formatCount, formatShare } from "../../lib/format";
import type { StorySlip } from "../ScrollStory";

export interface SeatLabel {
  nominations: number;
  wins: number;
  text: string;
  /** Which side of the seat the name sits on, always over empty seats. */
  side: "left" | "above" | "above-right";
}

export interface SweepStep extends StorySlip {
  highlight: (cell: SweepCell) => boolean;
  labels: SeatLabel[];
}

const everySeat = () => true;

const byYear = (films: FilmSummary[]) => [...films].sort((a, b) => a.year.localeCompare(b.year));

export function buildSteps({ totals, perfect, grid }: SweepData): SweepStep[] {
  const filmsIn = (match: (cell: SweepCell) => boolean) => byYear(grid.filter(match).flatMap((cell) => cell.films));

  return [
    {
      id: "seats",
      heading: "Every film gets a seat",
      body: `All ${formatCount(totals.films)} nominated films are seated here. The column is how many nominations a film earned, the row is how many it won, and bigger squares hold more films.`,
      highlight: everySeat,
      labels: [],
      plates: [],
    },
    {
      id: "empty-handed",
      heading: `${formatCount(totals.emptyHanded)} films won nothing`,
      body: `That is ${formatShare(totals.emptyHandedShare)} of every film ever nominated, and the front row is the fullest in the house. The Turning Point and The Color Purple each went 0 for 11.`,
      highlight: (cell) => cell.wins === 0,
      labels: [],
      plates: filmsIn((cell) => cell.wins === 0 && cell.nominations === 11),
    },
    {
      id: "top-row",
      heading: "Three films share the top row",
      body: "Ben-Hur (1959), Titanic (1997) and The Lord of the Rings: The Return of the King (2003) each won 11. No film has ever won 12.",
      highlight: (cell) => cell.wins === totals.maxWins,
      labels: [
        { nominations: 11, wins: 11, text: "The Return of the King", side: "left" },
        { nominations: 12, wins: 11, text: "Ben-Hur", side: "above" },
        { nominations: 14, wins: 11, text: "Titanic", side: "above" },
      ],
      plates: filmsIn((cell) => cell.wins === totals.maxWins),
    },
    {
      id: "perfect",
      heading: "Perfect nights are rare",
      body: `Only ${perfect.length} films with five or more nominations won every one: ${joinPerfect(perfect)}.`,
      highlight: (cell) => cell.wins === cell.nominations && cell.wins >= 5,
      labels: [
        { nominations: 11, wins: 11, text: "The Return of the King", side: "left" },
        { nominations: 9, wins: 9, text: "Gigi, The Last Emperor", side: "left" },
        { nominations: 5, wins: 5, text: "It Happened One Night", side: "above-right" },
      ],
      plates: byYear(perfect),
    },
    {
      id: "sinners",
      heading: "The record holder won four",
      body: "Sinners earned 16 nominations at the 98th ceremony, breaking the record of 14 held by All About Eve, Titanic and La La Land. It lost Best Picture to One Battle After Another.",
      highlight: (cell) => cell.nominations === totals.maxNominations,
      labels: [{ nominations: 16, wins: 4, text: "Sinners", side: "above-right" }],
      plates: filmsIn((cell) => cell.nominations === totals.maxNominations),
    },
    {
      id: "your-turn",
      heading: "Now pick a seat",
      body: "Tap any square to open its envelope and see which films are sitting there.",
      highlight: everySeat,
      labels: [],
      plates: [],
    },
  ];
}

function joinPerfect(perfect: SweepData["perfect"]) {
  const parts = perfect.map((film) => `${film.title} (${film.wins} for ${film.wins})`);
  return `${parts.slice(0, -1).join(", ")} and ${parts[parts.length - 1]}`;
}
