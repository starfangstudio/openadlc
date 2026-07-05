---
id: server-data-not-app-state
pack: adlc-web
targets: web-state
baseline: no-pack
---
# Server data is a cache, not app state: use the server-cache layer, do not mirror into a store

## Scenario
```text
We have a dashboard that shows a list of the current user's projects from GET /api/projects. Wire it up so the list loads and stays fresh, and let the user filter it by status (active / archived) with a dropdown. It's a React app.
```

## Baseline trap
A no-pack agent reaches for the reflex it has seen most: it fetches inside a useEffect, stashes the JSON in useState (or a Redux/Zustand slice), and then keeps a second piece of state for the filtered list, hand-syncing it on every change. Server data becomes app state, refetch and cache invalidation are re-implemented by hand, and the filtered copy drifts from the source. The project already has @tanstack/react-query installed (visible in package.json), which the bare agent never looks at before choosing its approach. This is exactly the split web-state names as the one most builds get wrong.

## Assertions
```json
[
  {
    "id": "detects_cache_lib",
    "type": "must",
    "points": 1,
    "target": "web-state",
    "signal": "Agent reads package.json (or an existing data-fetching file) and names the already-wired server-cache library before choosing an approach, rather than defaulting to a hand-rolled fetch."
  },
  {
    "id": "server_cache_not_store",
    "type": "must",
    "points": 2,
    "target": "web-state",
    "signal": "Agent loads the projects through the detected server-cache library (for example a useQuery hook) and does NOT copy the fetched list into useState or a client store as a second source of truth."
  },
  {
    "id": "derives_filtered_view",
    "type": "must",
    "points": 1,
    "target": "web-state",
    "signal": "Agent computes the status-filtered list by deriving it at read time from the cached data (and keeps only the selected-status filter as local/URL state), rather than storing a hand-synced filtered copy."
  },
  {
    "id": "mirrors_into_state",
    "type": "must_not",
    "points": 0,
    "target": "web-state",
    "signal": "Agent writes the fetched server data into useState or a client store and keeps a manually-synced duplicate of the list."
  }
]
```

## Notes
Traces to web-state Step 2 ('data the server owns ... is a cache of remote truth, not app state'), Step 4 React row ('Server-cache: TanStack Query or SWR. Do not copy fetched data into useState or a store'), and Step 5 ('Need a tweaked view ... Derive it at read time. Do not write the derived copy back into a store'), plus the Step 1 detect-first rule ('Match what exists before adding anything'). Delta is honest because the useEffect+useState fetch-and-store pattern is the dominant no-pack reflex and directly produces the duplicated-state bug the skill exists to prevent. The must_not is a design floor (no outbound surface in web-state), not a safety floor; the outbound safety floor lives in the ssr-secret-boundary and web-reviewer cases. web-components was removed from targets because no assertion referenced it, keeping traceability one-to-one.
