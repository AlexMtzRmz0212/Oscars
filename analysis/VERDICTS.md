# Story verdicts

What the data supports, from `story_claims.md`. Phase 4 writes copy from this file. Numbers cover competitive categories, through ceremony 98.

| Act | Verdict | Use this hook | Must also say |
|---|---|---|---|
| I. The Programme | Keep, sharpened | 12 categories at the first ceremony, a peak of 27 at the 23rd, 24 today. Casting arrived at the 98th. | Colour and black-and-white splits count as separate categories |
| II. The Sweep | Keep | Built and validated | |
| III. The Formula | Keep, new angle | Best Picture winners also won Directing 71 of 98 times. The most-nominated entrant won 85% of the time in 1970-89 and 31% since 2010. | Film Editing had no category before ceremony 7, so its early share is low by construction |
| IV. The Money | Rewrite | Median winner revenue fell from $667M in the 1990s to $257M in the 2010s and $105M since. In the 2010s the top-grossing nominee won 0 of 10 times. | Lifetime gross in 2025 dollars. Pandemic and streaming depress 2020 on. Never quote a single old film, because re-releases inflate it |
| V. The Audience Votes | Renamed, source changed to TMDb | The highest-rated nominee won 30 of 79 compared ceremonies (38%), about double the 18% chance rate. A private IMDb check agrees: 38 of 94 (40%) against 17%. | Scores are today's, and winning may lift a score, so this shows agreement, not cause. 19 ceremonies are left out because a nominee has under 50 TMDb votes, mostly before 1950 |
| VI. Who Gets the Gold | Keep, narrowed | Best Actor winners average 44.3, Best Actress 36.8. Women hold 9% of Directing credits since 2010 and were 0 of every Directing credit before Lina Wertmüller at the 49th. Three women have won Best Director. | Age is film year minus birth year. The gap is not steadily closing (+11.1, +6.8, +5.5, +8.0, +5.4 by era), so don't claim it is. Non-binary nominees are excluded from the two-way shares, not erased: say so |
| VI. Language | Keep | 19 of 617 Best Picture nominees weren't originally in English, and 11 of those came since 2010. Parasite and The Artist are the only winners. | The Artist is a largely silent French film |
| VII. Snubbed | Keep, one change | The Turning Point and The Color Purple went 0 for 11. Diane Warren is 0 for 17 competitively. John Williams is 5 for 54. | Counts exclude 82 rows the source marks as not official nominations, such as write-ins and withdrawn entries. That is also what brought Walt Disney to the published 59 nominations |

## Terms limits

- **IMDb:** its terms say data must not be republished or repurposed to build a movie database, except for personal use. It stays a private cross-check in `analysis/`, and nothing from IMDb is on the site. Film and person ids in the awards data are IMDb-format identifiers from the BSD-licensed source, not values taken from IMDb's files.
- **TMDb:** requires the exact notice line (in the footer) and a logo in the credits (Phase 5). Caching is capped at 6 months. Its terms also bar "derivatives" without defining them, which is worth reading against the Act IV charts before launch.

## Coverage limits

From `data/reports/coverage.md`:

- **Money:** Best Picture revenue is complete for 1990 to 2019, 95% for the 2020s and under 50% before 1950. All nominated films have only 41%, so money charts stay on Best Picture nominees.
- **Ages:** complete for acting nominees. Only 71% for people first nominated since ceremony 90, so age charts stay on acting.
- **Ratings and posters:** 99% of nominated films, so both are safe everywhere.
