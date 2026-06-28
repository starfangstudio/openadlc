---
name: owasp-mobile-security
version: 0.1.0
description: >
  This skill should be used when the user asks to "review a mobile app for security",
  "run an OWASP MASVS / MASTG audit", "check this Android/iOS app against mobile security
  standards", "is this app storing secrets safely", "audit certificate pinning / TLS",
  "check for insecure data storage", "review WebView / deeplink / IPC security", or otherwise
  wants a structured mobile-app security assessment grounded in OWASP MASVS, MASTG, and MASWE.
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# OWASP Mobile Security Review (MASVS / MASTG)

Audit a mobile app (Android or iOS) against the OWASP Mobile Application Security
standard. Produce findings mapped to MASVS controls and, where possible, the matching
MASWE weakness and MASTG test. Local, read-only by default.

## When to use
- Pre-release security pass on an Android/iOS feature or whole app.
- Triaging a suspected mobile vuln (insecure storage, weak crypto, missing pinning).
- Producing an auditable checklist against a recognized standard.

## Scope first (stop and confirm)
Confirm before starting:
1. **Platform(s)**: Android, iOS, or both. Native vs. hybrid/WebView vs. cross-platform.
2. **Profile**: which MASVS profiles apply, most apps target **L1** (baseline) + select
   **L2** (defense-in-depth) controls; add **R** (MASVS-RESILIENCE) only if the app must
   resist reverse engineering / tampering (e.g. handles high-value transactions, DRM, IP).
3. **Source access**: source tree, built artifact (`.apk`/`.aab`/`.ipa`), or both.
4. **Out of scope**: backend APIs, infra, flag but do not deep-dive unless asked.

If any are unknown, ask. Never invent the threat model.

## The eight MASVS control groups (review every one)
Walk each group; for each finding record **control → MASWE (if known) → evidence → fix**.

| Control | What to check |
|---|---|
| **MASVS-STORAGE** | Secrets/PII in SharedPreferences, plists, SQLite, files, logs, clipboard, screenshots, backups. Use Keystore/Keychain, not plaintext. |
| **MASVS-CRYPTO** | No hardcoded keys; strong algorithms (no MD5/SHA1/DES/ECB); secure random (`SecureRandom`, not `Random`); proper key management. |
| **MASVS-AUTH** | Biometric/MFA done right; no auth logic bypassable client-side; tokens stored securely; session handling. |
| **MASVS-NETWORK** | TLS only (no cleartext / `usesCleartextTraffic`); cert validation not disabled; certificate/public-key pinning where required. |
| **MASVS-PLATFORM** | IPC (exported components, intents, deeplinks), WebView (`addJavascriptInterface`, `setJavaScriptEnabled`, file access), pasteboard, screenshot/notification leakage, tapjacking. |
| **MASVS-CODE** | Out-of-date deps/CVEs; input validation; unsafe deserialization; debuggable flag; min platform version; injection sinks. |
| **MASVS-RESILIENCE** | (R profile only) root/jailbreak & debugger detection, anti-tamper/integrity, obfuscation, anti-hooking. Treat as defense-in-depth, never a substitute for L1/L2. |
| **MASVS-PRIVACY** | Data minimization, consent, permission necessity, third-party SDK data flows, identifiers/tracking. |

## Method
1. **Static pass.** Grep the source/manifest for the high-signal anti-patterns below. Read
   `AndroidManifest.xml` / `Info.plist` for exported components, cleartext, deeplinks,
   permissions, `android:debuggable`, `allowBackup`.
2. **Map each hit** to its MASVS control and, when identifiable, the MASWE id (e.g.
   hardcoded crypto key, SQL injection, insecure deeplink) and the MASTG test family.
3. **Dynamic pass (only if requested and runnable locally).** Note what would need a device
   or emulator (network capture, Frida, file inspection) rather than claiming a result.
4. **Verify before claiming.** A finding needs concrete evidence (file:line, manifest
   attribute, dependency version). Mark anything unconfirmed as `unverified`.

### High-signal static greps (Android examples)
```bash
# Cleartext / disabled TLS
grep -rniE 'usesCleartextTraffic|cleartextTrafficPermitted|ALLOW_ALL_HOSTNAME|trustAllCerts|X509TrustManager' --include='*.xml' --include='*.kt' --include='*.java' .
# Weak crypto & insecure randomness
grep -rniE '"(MD5|SHA-?1|DES|RC4)"|/ECB/|new[[:space:]]+Random\(' --include='*.kt' --include='*.java' .
# Hardcoded secrets
grep -rniE '(api[_-]?key|secret|password|token)[[:space:]]*[:=][[:space:]]*"[^"]+"' --include='*.kt' --include='*.java' --include='*.xml' .
# Risky WebView / IPC
grep -rniE 'addJavascriptInterface|setJavaScriptEnabled\(true\)|setAllowFileAccess\(true\)|MODE_WORLD_(READABLE|WRITEABLE)' --include='*.kt' --include='*.java' .
# Debuggable / backups
grep -rniE 'android:debuggable="true"|android:allowBackup="true"' --include='*.xml' .
```
Adapt sinks per platform/language (iOS: `NSUserDefaults`, `kSecAttrAccessible`,
`UIPasteboard`, `WKWebView` config, `Info.plist` ATS exceptions).

## Report format
Group findings by MASVS control, ordered by severity (Critical → Low):

```
## MASVS-NETWORK: Critical
Finding: Custom X509TrustManager accepts all certificates (TLS bypass).
Evidence: app/src/main/java/.../NetClient.kt:42
MASWE: improper certificate validation
MASTG test: MASTG-TEST network / cert validation family
Profile: L1
Fix: Remove the trust-all manager; use platform default trust + pinning if required.

## Summary
- Critical: N  High: N  Medium: N  Low: N
- Controls passed: STORAGE, CRYPTO, ...
- Not assessed (needs device/dynamic): ...
```

Always close with: what was **not** assessed and why (e.g. dynamic checks need an
emulator), so the gaps are explicit.

## Outbound needs the operator's explicit yes

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes"; see the global consent law.

## References
- OWASP MASVS: https://mas.owasp.org/MASVS/
- OWASP MASTG (tests, demos, techniques): https://mas.owasp.org/MASTG/
- OWASP Mobile App Security project: https://owasp.org/www-project-mobile-app-security/
- MASVS / MASTG / MASWE repos: https://github.com/OWASP/masvs , https://github.com/OWASP/mastg
