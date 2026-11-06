# Running the 99th season

The awards dataset updates weeks after each ceremony, so this season lives in these files. After each step, run `npm run data` and rebuild the site.

## Jan 21, 2027: nominations

Fill `nominees.csv` with **every category**, not only the six forecast. The model reads things like "also up for Film Editing" from the full ballot.

| Column | Example | Notes |
|---|---|---|
| `category` | `BEST PICTURE` | The canonical name, as listed in `public/data/categories/index.json` |
| `film_id` | `tt1234567` | IMDb-format id |
| `film_title` | `A Film` | |
| `nominee_ids` | `nm0000001\|nm0000002` | Use the person's existing id, so their career history counts |
| `nominee_names` | `A Person\|B Person` | Same order as the ids |
| `poster` | `/abc123.jpg` | Optional. A TMDb poster path |

Best Picture rows may leave the nominee columns empty.

## As precursors are announced

Add one row to `precursors.csv` per winner: the award key, the winner's id and their name.

- For acting and directing awards, the id is the person's. For film awards, it's the film's.
- For `dga`, add two rows, one for the director and one for the film.
- If the winner isn't an Oscar nominee, leave `id` empty. The page still counts that award as announced.

The award keys are in `CONTESTS` in `pipeline/predict.py`.

## Mar 13, 2027: freeze

From `pipeline/`:

```bash
python season.py freeze
```

This writes `frozen.json`. It refuses to run twice, and later changes to the files above can't touch it. Don't edit or delete it by hand.

## Mar 14, 2027: results

Add one row to `results.csv` per forecast category: the canonical category name and the winner's id, using the film id for Best Picture and the person id for the others. The page then scores the frozen forecast.

## After the dataset updates

When `DLu/oscar_data` includes the 99th ceremony, update the pin in `pipeline/fetch_awards.py`, add the 99th's precursors to the history, and retire these files.
