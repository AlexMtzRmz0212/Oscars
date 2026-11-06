export interface Meta {
  ceremonies: number;
  firstFilmYear: number;
  lastFilmYear: number;
}

export interface FilmSummary {
  id: string;
  title: string;
  year: string;
  poster: string | null;
}

export interface SweepCell {
  nominations: number;
  wins: number;
  count: number;
  films: FilmSummary[];
}

export interface SweepData {
  totals: {
    films: number;
    emptyHanded: number;
    emptyHandedShare: number;
    maxNominations: number;
    maxWins: number;
  };
  grid: SweepCell[];
  perfect: (FilmSummary & { wins: number })[];
}

export interface OvertureData {
  totals: { nominations: number; wins: number };
  columns: { ceremony: number; year: string; nominations: number; wins: number }[];
}

export interface ProgrammeData {
  ceremonies: { ceremony: number; year: string; total: number }[];
  families: { name: string; counts: number[] }[];
  facts: {
    first: number;
    latest: number;
    peak: number;
    peakCeremony: number;
    peakYear: string;
    everCategories: number;
    retired: number;
  };
}

export type FormulaFlag = "directing" | "editing" | "screenplay" | "acting" | "mostNominated";

export type FormulaWinner = FilmSummary & { ceremony: number; era: string } & Record<FormulaFlag, boolean>;

export interface FormulaData {
  winners: FormulaWinner[];
  eras: ({ era: string; winners: number } & Record<FormulaFlag, number | null>)[];
  totals: Record<FormulaFlag, number>;
}

export interface MoneyNominee {
  title: string;
  year: number;
  ceremony: number;
  winner: boolean;
  revenue: number;
  topGrosser?: boolean;
}

export interface MoneyData {
  nominees: MoneyNominee[];
  decades: {
    decade: number;
    medianWinner: number | null;
    winnersKnown: number;
    winners: number;
    nomineesKnown: number;
    nominees: number;
  }[];
  topGrosser: Record<"2010s" | "1990to2009", { won: number; ceremonies: number }>;
}

export interface AudienceNight {
  ceremony: number;
  year: number;
  era: string;
  size: number;
  rank: number;
  winner: FilmSummary & { rating: number };
  favourite: FilmSummary & { rating: number };
  gap: number;
}

export interface AudienceData {
  nights: AudienceNight[];
  ceremoniesCompared: number;
  ceremoniesTotal: number;
  chance: number;
  ranks: { rank: number; ceremonies: number }[];
  eras: { era: string; ceremonies: number; favouriteWon: number }[];
  widestGaps: AudienceNight[];
}

export interface AgeWinner {
  name: string;
  film: string;
  year: number;
  age: number;
}

export interface AgeGroup {
  winners: AgeWinner[];
  mean: number;
  median: number;
}

export interface GoldData {
  ages: { actor: AgeGroup; actress: AgeGroup };
  eraGaps: { era: string; actor: number | null; actress: number | null; gap: number | null }[];
  crafts: { craft: string; eras: { era: string; women: number; known: number; share: number | null }[] }[];
  eras: string[];
  directingWomen: {
    nominations: number;
    winners: { name: string; ceremony: number }[];
    first: { name: string; ceremony: number } | null;
  };
  language: {
    nominees: number;
    nonEnglish: number;
    byEra: { era: string; nonEnglish: number }[];
    winners: (FilmSummary & { language: string; ceremony: number })[];
  };
}

export interface SnubbedData {
  careers: {
    id: string;
    name: string;
    nominations: number;
    wins: number;
    points: { ceremony: number; nominations: number; wins: number }[];
  }[];
  films: (FilmSummary & { nominations: number })[];
  people: { id: string; name: string; nominations: number; honors: number }[];
}

export interface EncoreEntry {
  ceremony: number;
  year: string;
  picture: FilmSummary | null;
  director: string[];
  actor: string[];
  actress: string[];
}
