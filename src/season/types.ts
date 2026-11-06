export interface BacktestTally {
  hits: number;
  nights: number;
  hitRate: number | null;
  logLoss: number | null;
}

export interface BacktestData {
  firstYear: number;
  lastYear: number;
  trainingStarts: number;
  overall: Record<"model" | "mostNominated" | "precursorCount" | "chance", BacktestTally>;
  contests: {
    key: string;
    label: string;
    model: BacktestTally;
    mostNominated: BacktestTally;
    precursorCount: BacktestTally;
    chance: BacktestTally;
    nights: {
      ceremony: number;
      year: number;
      pick: string;
      pickProbability: number;
      winner: string;
      winnerProbability: number;
      correct: boolean;
    }[];
    weights: { feature: string; label: string; weight: number }[];
  }[];
  calibration: { from: number; to: number; nominees: number; predicted: number; actual: number }[];
}

export interface SeasonNominee {
  label: string;
  films: string[];
  people: string[];
  poster: string | null;
  link: string | null;
  probability: number;
  precursors: string[];
  won?: boolean;
}

export interface SeasonContest {
  key: string;
  label: string;
  awardsAnnounced: number;
  awardsTotal: number;
  nominees: SeasonNominee[];
  correct?: boolean | null;
}

export interface SeasonData {
  ceremony: number;
  filmYear: number;
  stage: "awaiting-nominations" | "open" | "frozen" | "scored";
  schedule: { label: string; date: string }[];
  frozenAt: string | null;
  score: { hits: number; nights: number } | null;
  contests: SeasonContest[];
}
