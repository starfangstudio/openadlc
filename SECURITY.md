<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Security Policy

OpenADLC is a security-adjacent tool: it governs what leaves your machine through human-in-the-loop lifecycle checkpoints, so we take reports seriously.

## Reporting a vulnerability

Do not open a public issue for a security problem. Instead:

- Use GitHub's private vulnerability reporting (the Security tab, "Report a vulnerability"), or
- Email security@openadlc.com.

Include what you found, how to reproduce it, and the impact. We will acknowledge, investigate, and coordinate a fix and disclosure with you.

## Scope

The lifecycle checkpoints are a deliberate human decision point, not a sandbox: the OS sandbox is the real boundary, and we never claim the checkpoints are unbypassable. Reports that demonstrate a lifecycle command pushing or posting outbound without an explicit human approval, or blocking benign local work, are especially welcome.

## Supported versions

Pre-1.0: only the latest release is supported.
