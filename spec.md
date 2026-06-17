# 2026 FIFA World Cup Matches Website Spec

## Goal

Build a small Python website that shows only the 2026 FIFA World Cup match information the user cares about:

- Date
- Time
- Venue
- Teams
- Group or knockout stage
- Score, only when the match has already been played

No news, standings, squad information, scorers, TV listings, commentary, images, ads, or long tournament text.

## Recommended Data Source

Use Wikipedia as the first implementation source.

Primary page:

- https://en.wikipedia.org/wiki/2026_FIFA_World_Cup

Supporting pages if needed:

- Group pages such as `https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_A`
- Knockout page: `https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_knockout_stage`

Reasoning:

- Wikipedia exposes predictable HTML tables that Python can read with `pandas.read_html`, `BeautifulSoup`, or `mwparserfromhell`.
- The current Wikipedia page includes group stage and knockout sections, and the source notes that match times are local.
- The official FIFA scores/fixtures page is authoritative, but it is a modern dynamic page and may be harder to scrape reliably without reverse-engineering client-side data calls.

Official reference page:

- https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/scores-fixtures

## Easier Alternatives

For a no-login, low-friction Python implementation, Wikipedia is probably the easiest practical source.

Other options:

- FIFA official page: best authority, worse scraping ergonomics because the page is dynamic.
- Paid or key-based football APIs: potentially cleaner JSON, but require account setup, rate-limit handling, and checking whether the 2026 World Cup is included.
- News or TV schedule articles: easier to read manually, but not a stable data source for an app.

Recommendation: start with Wikipedia, structure the code so the scraper can be replaced later with an official/API source if needed.

## User Experience

The first screen should be the fixture list itself, not a landing page.

Layout:

- Simple table or compact grouped list.
- Matches sorted by kickoff date/time.
- Group matches labeled as `Group A`, `Group B`, etc.
- Knockout matches labeled as `Round of 32`, `Round of 16`, `Quarterfinal`, `Semifinal`, `Third place`, or `Final`.
- Played matches show a score.
- Future matches show a muted placeholder such as `-`.

Suggested columns:

| Date | Time | Stage | Teams | Score | Venue |
| --- | --- | --- | --- | --- | --- |
| 2026-06-11 | 20:00 | Group A | Mexico vs South Africa | 2-0 | Mexico City Stadium |

Controls:

- Search box for team, venue, or stage.
- Stage filter: `All`, `Groups`, `Knockout`.
- Optional group filter: `All`, `A` through `L`.
- Optional toggle: `Hide future matches`.

Keep the UI plain and readable. This is a data page, not a promotional site.

## Technical Approach

Use Python.

Recommended stack:

- Backend: Flask
- Scraping/parsing: `requests`, `beautifulsoup4`, `pandas`, `lxml`
- Cache: local JSON file, refreshed on demand or every few hours
- Frontend: server-rendered HTML template with minimal CSS and JavaScript

Suggested project structure:

```text
try_world_cup/
  app.py
  worldcup/
    __init__.py
    scrape.py
    normalize.py
    cache.py
  templates/
    index.html
  static/
    styles.css
  data/
    matches.json
  tests/
    test_normalize.py
  spec.md
```

## Data Model

Normalize every match into this shape:

```json
{
  "date": "2026-06-11",
  "time": "20:00",
  "timezone_note": "local venue time",
  "stage": "Group A",
  "team_1": "Mexico",
  "team_2": "South Africa",
  "score": "2-0",
  "venue": "Mexico City Stadium",
  "status": "played",
  "source_url": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup"
}
```

Status values:

- `scheduled`
- `played`
- `unknown`

For knockout placeholders, teams can be names or unresolved labels such as `Winner Group A` until updated.

## Scraping Rules

Parser should:

- Fetch the Wikipedia page.
- Extract only match tables from group stage and knockout sections.
- Ignore standings, rankings, squad tables, statistics, disciplinary tables, references, and prose.
- Normalize dates to ISO format: `YYYY-MM-DD`.
- Preserve kickoff time as shown by the source.
- Preserve venue text as shown by the source.
- Detect scores only when a score exists in the match row.
- Sort all rows by date and time.
- Store the normalized output in `data/matches.json`.

Avoid hard-coding all 104 matches unless scraping proves unreliable. A few fallback mappings are acceptable for stage labels or venue cleanup.

## Refresh Behavior

Default behavior:

- Use cached `data/matches.json` when available.
- Refresh cache when the user visits `/refresh` or when the cache is older than a configured age.

Suggested environment variable:

```text
WORLD_CUP_CACHE_TTL_SECONDS=10800
```

This defaults to 3 hours.

## Routes

`GET /`

- Shows the match list.
- Uses cached data unless refresh is needed.

`GET /refresh`

- Re-fetches Wikipedia.
- Rebuilds `data/matches.json`.
- Redirects back to `/`.

`GET /api/matches`

- Returns normalized JSON for debugging or future frontend use.

## Error Handling

If scraping fails:

- Continue serving the last cached match list if it exists.
- Show a small status message near the top: `Showing cached data; refresh failed.`
- Log the error server-side.

If no cache exists and scraping fails:

- Show a simple error page explaining that match data could not be loaded.

## Testing

Minimum tests:

- Date normalization.
- Score detection.
- Played vs scheduled status detection.
- Sorting by date/time.
- Filtering by group/stage.
- Parser fixture test using saved HTML snippets from Wikipedia.

Do not make tests depend on live Wikipedia responses.

## Implementation Plan

1. Create Flask app skeleton.
2. Build scraper that fetches and parses Wikipedia into normalized match dictionaries.
3. Add JSON cache read/write.
4. Render simple table UI.
5. Add search/filter controls.
6. Add `/refresh` and `/api/matches`.
7. Add focused parser and normalization tests.
8. Run locally and verify the page with current data.

## Open Decisions Before Implementation

- Should times be shown exactly as source local time, or converted to the user's local timezone?
- Should the table include the source update time?
- Should future knockout teams show placeholders, or should unresolved rows be hidden until teams are known?

Recommended defaults:

- Show times exactly as source local time.
- Include a small `Last refreshed` timestamp outside the table.
- Show unresolved knockout rows because they are still valid scheduled matches.
