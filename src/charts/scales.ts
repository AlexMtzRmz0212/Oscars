export type Scale = (value: number) => number;

export const linearScale = ([d0, d1]: [number, number], [r0, r1]: [number, number]): Scale => (value) =>
  r0 + ((value - d0) / (d1 - d0)) * (r1 - r0);

export const logScale = ([d0, d1]: [number, number], [r0, r1]: [number, number]): Scale => {
  const span = Math.log(d1) - Math.log(d0);
  return (value) => r0 + ((Math.log(value) - Math.log(d0)) / span) * (r1 - r0);
};

/** Keeps a tooltip inside its chart. */
export const clamp = (value: number, low: number, high: number) => Math.min(Math.max(value, low), Math.max(low, high));
