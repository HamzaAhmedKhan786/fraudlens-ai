# Enterprise interface redesign

## Audit and implementation sequence

The App Router has 20 existing product screens and server-side API proxies. Cases, uploads,
Gmail, review decisions, comments, deletion/restore and the two copilots can be reused.
The dashboard duplicated the application shell, retained a fixed personal identity and health
claims, and fetched entire case collections for metrics. Existing CSS/Lucide components are
retained and extended with shared design tokens, tables, charts, cards and navigation.
Tailwind/PostCSS adds utility primitives and reusable empty states alongside the existing CSS.
Native SVG charts avoid an additional chart package. The lazy-loaded world basemap uses
D3 Geo, TopoJSON Client and pinned World Atlas 2.0.2 country boundaries, packaged locally.
Country outlines, selection, tooltips, zoom and keyboard pan work without location services.

1. Shared teal/navy design system and accessible application shell.
2. Tenant-scoped SQL aggregates, daily analytics and server-paginated case search.
3. Connected dashboard, investigation workspace and evidence intake.
4. Route-aware documentation help drawer, citations and feedback.
5. Production build, targeted authorization tests and responsive browser verification.

## Feature inventory

| Capability | Audit status | Interface treatment |
| --- | --- | --- |
| Cases, evidence, deterministic investigations, reports | Implemented | Reuse APIs and scoring |
| Review, audit, soft delete and recovery | Implemented | Preserve controls and decisions |
| Gmail/OCR/malware scan | Configuration required | Show actual statuses and errors |
| OIDC, memberships, subscriptions, test billing | Configuration required | Resolve identity server-side; preserve gates |
| Case copilot and product documentation guide | Implemented foundations | Separate evidence chat and help drawer |
| Dashboard historical analytics | Partial | Add bounded aggregation endpoint |
| World basemap | Implemented | Local country outlines, selection, zoom, keyboard pan |
| Geographic risk | Unavailable: no verified geographic schema | Basemap visible; risk layer explicitly inactive |
| Model health | Configuration/readiness, not active probe | Label as configuration status |
| Outlook add-ins, validated media models | Planned/experimental | Preserve unavailable labels |
| SAR, transactions, sanctions and compliance percentages | Not implemented | Excluded |

## Data and interface contracts

`GET /analytics/overview?days=7|30|90` aggregates tenant-owned, non-deleted cases, runs and
uploads. Trend creation uses stored timestamps; completed runs use their recorded creation
timestamp because a separate completion timestamp is not available. High-risk series counts
runs with persisted HIGH/CRITICAL severity, not a fabricated count of individual findings.
Evidence processing uses upload update dates for current processed records; it is not a full
event history. Cards display dashes on failure and zero only after a successful empty response.

`GET /cases/search` performs bounded search/filter/sort/page queries. Existing `/cases` and
`/dashboard` contracts remain intact. All aggregation/search queries filter tenant and soft
deletion before collecting results. Charts use native accessible SVG and CSS without a large
chart dependency. Country boundaries display independently of risk records. Geographic
indicators remain absent until trusted location data exists; hovering a country never implies
that a case or threat was observed there. World Atlas attribution and license are included in
`apps/web/public/maps/`. The dataset source is https://github.com/topojson/world-atlas.

The help drawer sends the current route as navigation context only, renders safe Markdown,
validates citation IDs, and keeps session chat scoped to the current workspace. Helpful/
unhelpful feedback stores document IDs/revisions in the existing audit infrastructure, not
case evidence. Product guide feedback does not train models.

## Verification and boundaries

- Production build: Next.js 16.4.2, all routes generated, TypeScript checked.
- Backend regression: 21 tests passed across API, orchestrator, analytics, knowledge access,
  security/copilot/billing suites. Ruff passed. npm audit reported zero vulnerabilities.
- Browser checks: desktop 1280/1440px and mobile 390px; real case search, severity filter,
  sorting, empty state, investigation dialog, documentation citations/feedback, evidence upload,
  and country selection/zoom/reset. No console warnings/errors in the final preview.
- The basemap contains 177 country shapes and is served locally, not by a third-party tile API.
  The previous geographic panel only rendered an unavailable-data message: it had no country
  geometry to draw. Country boundaries are now independent of the still-unavailable risk layer.
- Screenshots in `screenshots/enterprise-redesign/` use an isolated SQLite preview with synthetic
  cases and a generated, non-sensitive text upload. They are not production fraud statistics.

External OAuth, identity-provider, payment, malware-scanner and media-model configuration is
unchanged. Those integrations were not activated or certified by these UI checks. The active
user checkout and its uncommitted edits were not overwritten; development and validation ran
in the attached managed worktree.
