<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Tracker adapters (ADLC)

ADLC commands talk to a tracker through ONE small abstraction, not GitHub-specific commands sprinkled through the prose. The lifecycle says "create the issue, link it under the parent, set it in-progress, assign the operator"; the adapter turns each of those into the right call for whatever tracker the workspace uses. Swap the tracker, keep the lifecycle. Loaded by intake, plan, and implement, and cited from [references/run-isolation.md](references/run-isolation.md) wherever a tracker write happens.

## The four verbs (the whole interface)
Every tracker action in ADLC is one of these four. Commands call the verb; they never name a tracker.

| Verb | What it does | Inputs |
|---|---|---|
| `create_issue` | Create an issue/work item, assign the operator on create (F6), and return its id | title, body (two faces, see below), assignee, labels/type |
| `link_child` | Attach a child issue as a NATIVE child of a parent (F7), not a text mention | parent id, child id |
| `set_status` | Move an item to a declared status, e.g. in-progress at implement start (F8) | item id, status name |
| `assign` | Set or change the assignee of an existing item | item id, assignee |

Two rules hold for all four:
- **The body carries both faces (F5).** `create_issue` posts the human face as the issue body AND the full AI face inside a collapsible `<details><summary>Full AI context (for /agentic-plan and implementers)</summary> ... </details>` block, plus a one-line pointer to the run workspace. The content is INLINE; never post only a `~/.openadlc/...spec.md` path (a teammate, CI, or fresh agent cannot read a path on someone else's disk).
- **Every verb is outbound, so every verb stops at the consent checkpoint.** The agent assembles the call locally, shows the operator exactly what would go out, and waits for an explicit yes before it fires. There is no standing approval. This is a stop-and-ask the agent performs, not a hook.

## Status names are declared, never invented
`set_status` only accepts statuses the adapter declares for that tracker. ADLC uses a small canonical set and the adapter maps each to the tracker's real value:

| Canonical status | When | Notes |
|---|---|---|
| `in-progress` | start of /agentic-implement, after the sub-issue resolves (F8) | the one this spec requires today |
| `in-review` | a PR is open and under review | optional, tracker permitting |
| `done` | the PR merged | optional, tracker permitting |

If a tracker lacks a status, the adapter maps to the nearest real one or no-ops with a note; it never makes up a value inline.

## Per-tracker mappings

### GitHub (issues + sub-issues API + labels / Projects)
- **create_issue:** `gh issue create --title "<title>" --body-file <body> --assignee @me` (F6). The body file holds both faces. If `@me` does not resolve to the operator's account, ask once who to assign and reuse it for the run. Capture the new issue's number and node id from the response.
- **link_child (native sub-issue, F7):** `gh api -X POST /repos/{owner}/{repo}/issues/{parent}/sub_issues -F sub_issue_id={child_node_id}`, or the GraphQL `addSubIssue` mutation. This makes a real GitHub sub-issue; a "child of #N" line in the body does NOT.
- **set_status:** apply a `status: in progress` label, or set the status field on the GitHub Project the item is on (`gh project item-edit`). Pick one per workspace and keep it consistent.
- **assign:** `gh issue edit <n> --add-assignee <login>` (`@me` for the operator).
- **Attachments:** GitHub issues take no file attachments via the API, so the two faces live INLINE in the body and the plan files stay in the run workspace, referenced by run-id (per run-isolation).

### Jira (issues + sub-tasks + status transitions + assignee)
- **create_issue:** create the issue with its `issuetype`, set `assignee` to the operator on create (F6). The description holds both faces (Jira renders an expand/collapse panel for the AI face).
- **link_child (native sub-task, F7):** create the child as issuetype `Sub-task` with its `parent` field set to the parent key (or convert an existing issue to a sub-task of the parent). This is Jira's native hierarchy, not a linked-issue mention.
- **set_status:** drive the workflow `transition` whose target maps to the canonical status (e.g. `in-progress` -> the project's "In Progress" transition). Transitions are project-specific; the adapter reads the available transitions, it does not assume names.
- **assign:** set the `assignee` field (accountId) on the issue.
- **Attachments:** Jira accepts attachments, so plan files MAY be attached in addition to the inline two faces; the run workspace stays the source of truth.

### Azure DevOps (work items + parent/child links + state + assigned-to)
- **create_issue:** create the work item of the right type (User Story, Bug, Task), set `System.AssignedTo` to the operator on create (F6). The description holds both faces.
- **link_child (parent/child link, F7):** add a `System.LinkTypes.Hierarchy-Forward` link from the parent work item to the child (or `Hierarchy-Reverse` from child to parent). This is ADO's native parent/child tree.
- **set_status:** set `System.State` to the value mapped from the canonical status (e.g. `in-progress` -> "Active" or "Doing", depending on the process template). The adapter maps per template; it never writes a raw state name the board does not have.
- **assign:** set `System.AssignedTo` on the work item.
- **Attachments:** ADO accepts attachments, so plan files MAY be attached alongside the inline two faces; the run workspace stays canonical.

## Adding a tracker
A new tracker is a new column in the tables above: define how it maps `create_issue` (with assign-on-create + two faces), `link_child` (its native child relation), `set_status` (its real status/state values), and `assign`. Commands change nothing. If a verb has no native equivalent, map to the nearest real behavior or no-op with a visible note; never silently drop a write and never fake hierarchy with text.

---

Author: OpenADLC core. Freshness: written for the v0.1 four-verb adapter (GitHub, Jira, ADO). The GitHub sub-issues API and the per-tracker status/state names drift, re-verify the `gh api` sub-issues route, the Jira transition names, and the ADO state values against the live tracker before relying on them.
