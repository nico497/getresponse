# GetResponse · Head-to-Head Radar

Static page (GitHub Pages, served from `/docs`) comparing what AI tools tell online store owners about GetResponse vs one competitor at a time.

**Current state:** test build with sample data. No API calls. Only the Klaviyo matchup is filled in.

## Structure

```
docs/
  index.html          the page (switch rivals with the top buttons or #klaviyo, #mailchimp …)
  data/rivals.json    which competitors appear in the switcher
  data/<rival>.json   one file per matchup
  fonts/              Archivo (SIL Open Font License)
```

## Data format (`data/<rival>.json`)

A file with `"pending": true` shows a "not run yet" state. A filled file has:

| Key | What it holds |
| --- | --- |
| `sample` | `true` shows the sample-data banner |
| `collected`, `market` | stamp in the header, e.g. `"Nov 2026"`, `"US, logged out"` |
| `headline` | `lead` sentence and 3 `points` (`text`, `chips`, optional `youChip` index) |
| `priority[]` | ranked features: `feature`, `need` (1–5), `ai` (what AI says), `verdict` (`outdated` / `holds` / `unclear`), `reason` |
| `scoreboard[]` | per engine: `engine`, `mode`, `gr`, `rival`, `none` (forced picks out of 10), `split` (true if the pick changes with name order) |
| `strengths` | `gr[]` and `rival[]`: `label`, `n` (answers out of 40 crediting it) |
| `consensus[]` | `claim` + `counts` per engine (`claude`, `chatgpt`, `gemini`, `google`, out of 10) |
| `prompts[]` | the 10 prompts, same for every engine |
| `answers` | per engine: `note` + `rows[]` of `[pick, main reason, sources cited]`, one per prompt |
| `retest[]` | `claim`, `train`/`trainOf` (search off), `live`/`liveOf` (search on + Google), `check`, `url`, `verdict` |
| `gapNote` | the summary under the retest table |

## Next step: live data

Replace the sample files with output from scripted runs (Claude, ChatGPT, Gemini APIs with search off and on, plus Google results), writing the same JSON shape. The page needs no changes.
