<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
---
id: two-domain-activates-both
scenario: a repo matching two technical domains activates both matched packs
slice: S-A3 (B-172)
checked_by: tools/check-activation-redproves.py::redprove_1_two_domain_activates_both
fixture_dir: tools/test/domains/fixtures/fx-multi
---

## Starting condition

A repo (`tools/test/domains/fixtures/fx-multi`) contains:
- `package.json` with a `react` dependency (matches the `web` marker,
  `standard/domains.md` § 2)
- `Dockerfile` (matches the `backend-cloud` marker, `standard/domains.md` § 2)

Stage 1 (the deterministic repo-facts sniff, `standard/domains.md` § 4) matches
this repo to `{web, backend-cloud}`. Neither marker is exclusive of the other:
this is not a monorepo edge case, it is the ordinary case of a containerized
web app.

## Expected observable behavior

Stage 2 (`plugins/adlc-core/commands/ai-implement.md` § 0) computes
`candidate_set ∩ matched_domains` as a UNION over every matched domain, not a
pick-one. With the default candidate set (untweaked, all packs approved), the
activated pack set is:

```
FLOOR ∪ {adlc-web, adlc-backend-cloud}
= {adlc-core, adlc-security, adlc-web, adlc-backend-cloud}
```

Both `adlc-web` AND `adlc-backend-cloud` load; neither matched domain is
dropped because another one also matched.

## Assertion

`adlc-web ⊆ activated AND adlc-backend-cloud ⊆ activated`, over the floor
plus both matched packs.

**TEETH:** a "single-domain" stub of stage 2 (keeps only `sorted(matched)[0]`,
i.e. picks one match and silently drops the rest) is run against this same
fixture first. It activates only `{adlc-core, adlc-security,
adlc-backend-cloud}`, missing `adlc-web`, and the assertion correctly FAILS
under that stub. The correct funnel (union over the full intersection) is
then run against the same fixture and the assertion PASSES. See
`tools/check-activation-redproves.py` for the RED-then-GREEN output.
