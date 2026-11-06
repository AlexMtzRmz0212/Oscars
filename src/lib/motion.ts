/** The entrance every section part uses: a short rise, once, as it comes into view. */
export const rise = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.2 },
  transition: { duration: 0.6, ease: [0.2, 0.8, 0.2, 1] },
} as const;

export const riseAfter = (index: number) => ({
  ...rise,
  transition: { ...rise.transition, delay: index * 0.07 },
});
