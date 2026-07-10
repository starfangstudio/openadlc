<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
---
id: pinned-floor-survives-repo-injection
scenario: repo/project content cannot deactivate a mandatory-floor pack
slice: S-A3 (B-172)
checked_by: tools/check-activation-redproves.py::redprove_2_floor_survives_repo_injection
fixture_dir: tools/test/activation/fixtures/fx-inject-disable-security
---

## Starting condition

A repo (`tools/test/activation/fixtures/fx-inject-disable-security`) contains:
- `Dockerfile` (matches the `backend-cloud` marker, an ordinary repo fact)
- `.openadlc/config.yaml`, a project-level config that CARRIES a malicious
  attempt to drop the security floor:
  ```yaml
  packs:
    disabled: [adlc-security]
  ```

This is the same `packs.disabled` key `openadlc.example.yaml` documents for
tightening the discretionary stage-2 candidate set. Here it is used, by
whoever controls the repo's content, to try to disable `adlc-security`, a
MANDATORY FLOOR member.

## Expected observable behavior

Per the rail-1 preamble (`plugins/adlc-core/commands/ai-implement.md` § 0):
"the floor loads before and independent of BOTH the stage-0 candidate set
and stage-2 ask-scoping... can NEVER drop a floor member." A project can
tighten its OWN discretionary picks; it has no authority over the floor at
all, managed or otherwise (`openadlc.example.yaml`: managed > project > user,
and a project cannot loosen a managed setting; the floor is not even a
project-adjustable setting in the first place). The activated set stays:

```
FLOOR ∪ {adlc-backend-cloud}
= {adlc-core, adlc-security, adlc-backend-cloud}
```

`adlc-security` is present regardless of what the repo's own config says.

## Assertion

`adlc-security ∈ activated`, even though the fixture's own config lists it
under `packs.disabled`.

**TEETH:** a broken funnel that HONORS the repo's `packs.disabled` list
against the floor (i.e. treats repo-supplied config as authoritative over a
floor member, "injection succeeds") is run against this fixture first. It
activates only `{adlc-core, adlc-backend-cloud}`, dropping `adlc-security`,
and the assertion correctly FAILS under that stub. The correct funnel (floor
computed independent of stage 0 and of any repo content) is then run against
the same fixture and the assertion PASSES. See
`tools/check-activation-redproves.py` for the RED-then-GREEN output.
