const integer = new Intl.NumberFormat("en-US");

export const formatCount = (value: number) => integer.format(value);

export const formatShare = (share: number) => `${(share * 100).toFixed(1)}%`;

export const formatPercent = (share: number) => `${Math.round(share * 100)}%`;

export const plural = (count: number, one: string, many = `${one}s`) =>
  `${formatCount(count)} ${count === 1 ? one : many}`;

export function formatDollars(value: number) {
  if (value >= 1e9) return `$${(value / 1e9).toFixed(value >= 1e10 ? 0 : 1)}B`;
  if (value >= 1e6) return `$${Math.round(value / 1e6)}M`;
  return `$${Math.round(value / 1e3)}K`;
}

export const joinNames = (names: string[]) =>
  names.length < 2 ? names.join("") : `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;

export const ordinal = (value: number) => {
  const tens = value % 100;
  const suffix = tens >= 11 && tens <= 13 ? "th" : { 1: "st", 2: "nd", 3: "rd" }[value % 10] ?? "th";
  return `${value}${suffix}`;
};
