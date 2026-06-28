---
name: adlc-security-review
description: "This command should be used when the user types \"/adlc-security-review\", or asks to \"do a security review\", \"scan this diff for vulnerabilities\", \"check this change for security issues\", \"review for injection/secrets/authz bugs\", or \"security-check before I push\". Wraps the built-in security-review to scan the local diff for vulnerabilities, then stops and asks the operator for an explicit yes before any outbound write (PR comment, issue, posted report)."
version: 0.1.0
disable-model-invocation: true
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
<!-- Outbound gh writes are NOT pre-approved: stop and get the operator's
     explicit yes before any of them. -->

# /adlc-security-review

Thin ADLC wrapper over the **built-in `security-review`** command (renamed from `/security-review` to avoid colliding with the built-in of that name). The underlying
command does the work, analyze the diff/PR for vulnerabilities and print findings.
This wrapper adds ONE thing: scanning and reporting are local and need no approval, but
**posting any finding back to GitHub or anywhere on the internet STOPS and asks the operator for an explicit yes first.**

Target (diff, PR number, URL, or empty for the working tree): $ARGUMENTS

## Pipeline: what this loads, start → finish
1. built-in **`security-review`** runs the vulnerability pass → (optionally) **`static-code-scanner`** for SAST + secret scan → 2. print findings → 3. **🚦 stop and ask the operator for an explicit yes** before posting anything.
- **Models:** Sonnet; Opus for a deep audit. Never Haiku.
- **Outbound:** only the post, and only after the operator's explicit yes.

## What to do

1. **Run the built-in `security-review`** against `$ARGUMENTS` (or the current working
   tree / staged diff if empty). Let it do the full vulnerability pass, injection,
   authn/authz, secrets, SSRF, path traversal, unsafe deserialization, crypto misuse,
   and the rest of its checklist. Do not re-implement its analysis here.

2. **Keep everything local.** Reading code, running the scan, and printing findings need
   no approval. Print the built-in's findings to the terminal exactly as produced.

3. **Stop before any outbound action.** If the user asked to post findings to a PR or
   issue (comments, a review verdict, a posted summary), DO NOT post yet, go to the
   checkpoint below.

## 🚦 Stop and ask the operator, before any GitHub or internet write

Posting comments, a review verdict (`--approve` / `--request-changes`), an issue, or any
summary to a remote is an outbound action under the ADLC consent law.

- Present the findings report and ask plainly: *"Post these N security findings to PR #X?"*
- **Wait for an explicit "yes".** No implied or standing approval. No autonomous posting.
- Only after "yes": post exactly what was shown, nothing added, nothing omitted.
- A security review that surfaces a real vulnerability is sensitive: never disclose it
  outside this machine (issue tracker, chat, email) without the same explicit "yes".

## Guardrails

- Scan/analyze/print locally; the only outbound step is the post above, after the operator's explicit yes.
- Never run `gh pr comment`, `gh pr review`, `gh issue comment`, or `gh api` writes before
  the operator says "yes" to the presented report.
- Report findings as `path:line` with a severity. Mark anything unconfirmed `unknown`: never invent a vulnerability or a fix.

## References

- Built-in command wrapped: `security-review` (Claude Code).
- Claude Code: Security review: https://code.claude.com/docs/en/security
- OWASP Top Ten (vulnerability taxonomy the scan covers): https://owasp.org/www-project-top-ten/
