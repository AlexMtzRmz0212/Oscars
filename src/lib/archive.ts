import type { FilmSummary } from "./types";

const SHARD_COUNT = 100;

/** Matches shard_of in pipeline/explore.py. */
export function shardOf(id: string) {
  let sum = 0;
  for (const character of id) sum += character.charCodeAt(0);
  return String(sum % SHARD_COUNT).padStart(2, "0");
}

export type NomineeType = "person" | "company" | "unknown";

export interface EntryNominee {
  id: string;
  name: string;
  type: NomineeType;
}

export interface Entry {
  ceremony: number;
  year: string;
  category: string;
  slug: string;
  competitive: boolean;
  winner: boolean;
  unofficial?: boolean;
  films: { id: string; title: string }[];
  nominees: EntryNominee[];
  detail?: string;
  note?: string;
  citation?: string;
}

export interface CeremonyIndexRow {
  ceremony: number;
  year: string;
  bestPicture: FilmSummary | null;
}

export interface CeremonyPageData {
  ceremony: number;
  year: string;
  competitiveCategories: number;
  bestPicture: FilmSummary | null;
  categories: { name: string; slug: string; family: string; competitive: boolean; entries: Entry[] }[];
}

export interface CategoryIndexRow {
  slug: string;
  name: string;
  family: string;
  competitive: boolean;
  firstCeremony: number;
  lastCeremony: number;
}

export interface CategoryPageData extends CategoryIndexRow {
  ceremonyCount: number;
  nights: { ceremony: number; year: string; nominees: number; winners: Entry[] }[];
  leaders: { id: string; name: string; type: NomineeType; wins: number; nominations: number }[];
}

export interface FilmPageData extends FilmSummary {
  nominations: number;
  wins: number;
  honors: number;
  rating: number | null;
  votes: number | null;
  runtime: number | null;
  genres: string[];
  language: string | null;
  countries: string[];
  budget: number | null;
  revenue: number | null;
  rank: { rank: number; of: number; ceremony: number } | null;
  entries: Entry[];
}

export interface PersonPageData {
  id: string;
  name: string;
  type: NomineeType;
  nominations: number;
  wins: number;
  honors: number;
  birthYear: number | null;
  firstCeremony: number;
  lastCeremony: number;
  partners: (EntryNominee & { shared: number })[];
  entries: Entry[];
}

export const filmHref = (id: string) => `/films/${id}`;
export const ceremonyHref = (ceremony: number) => `/ceremonies/${ceremony}`;
export const categoryHref = (slug: string) => `/categories/${slug}`;
export const bornHref = (year: number) => `/born/${year}`;
export const nomineeHref = (nominee: { id: string; type: NomineeType }) =>
  nominee.type === "company" ? `/studios/${nominee.id}` : `/people/${nominee.id}`;
