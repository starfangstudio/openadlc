---
name: webview-engineering
description: "This skill should be used when building, hardening, or reviewing Android in-app web content, when the user mentions \"WebView\", \"WebViewClient\", \"WebChromeClient\", \"JavaScript bridge\", \"addJavascriptInterface\", \"shouldInterceptRequest\", \"Custom Tabs\", \"in-app browser\", \"content scripts\", \"WebMessageListener\", or \"WebView security\". Covers stock Android WebView (primary) and the engine-abstraction pattern for swapping in GeckoView."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Android WebView engineering

Build secure, crash-resilient in-app web experiences. This skill encodes the production patterns observed in a privacy-focused Android browser (a stock-WebView, privacy-hardened browser). For the concrete class-by-class breakdown, read [references/webview-architecture.md](references/webview-architecture.md).

## Step 1: Choose WebView vs Custom Tabs first

Decide before writing code:

- **WebView**: hosting *your own* content, injecting JavaScript, or needing a native↔web bridge / full layout integration. You own security hardening and lifecycle.
- **Custom Tabs**: sending the user to *external* URLs you don't own (including OAuth). Shares cookies/state with the user's default browser, gets Safe Browsing, less to maintain.

Rule of thumb: **own content → WebView; someone else's site → Custom Tabs.** If both are needed, detect intent at the call site (see the reference app's `CustomTabDetector`).

## Step 2: Build on a hardened custom WebView subclass

Subclass `WebView` so configuration and crash-safety live in one place:

- Guard `destroy()`, `stopLoading()`, `onPause()` with an `isDestroyed` flag, a destroyed WebView that still receives calls crashes.
- Disable keyboard/typing personalisation for privacy where appropriate.
- Configure `WebSettings` explicitly; do not rely on defaults for security-relevant flags (Step 4).

## Step 3: Use a `WebMessageListener` JS bridge, not `addJavascriptInterface`

Prefer `androidx.webkit` `WebViewCompat.addWebMessageListener(...)` with `JavaScriptReplyProxy`:

- It is **origin-scoped**: the bridge is only exposed to the allow-listed origins you specify, not every frame.
- It avoids the reflection-based attack surface of `addJavascriptInterface`.

If `addJavascriptInterface` is unavoidable: target API 21+, annotate exposed methods with `@JavascriptInterface`, expose the **minimum** surface, and `removeJavascriptInterface(...)` before loading untrusted content.

For a full multi-feature bridge (a shared message contract with a **secret token**, an **origin allow-list**, document-start injection, and per-feature handler plugins), see [references/js-bridge-and-content-scripts.md](references/js-bridge-and-content-scripts.md).

## Step 4: Harden the WebView (checklist)

Copy this checklist into the task and verify each item:

```
WebView hardening:
- [ ] Local assets served via WebViewAssetLoader (https scheme), never file://
- [ ] setAllowFileAccessFromFileURLs = false; setAllowUniversalAccessFromFileURLs = false
- [ ] setAllowFileAccess restricted (false unless a specific need is justified)
- [ ] JS bridge is origin-scoped (WebMessageListener) or interface surface is minimal + removed before untrusted loads
- [ ] shouldInterceptRequest validates/inspects every resource (see Step 5)
- [ ] HTTPS enforced/upgraded; mixed content not allowed
- [ ] onRenderProcessGone handled (see Step 6)
- [ ] SSL errors handled explicitly, never blanket-proceed (see Step 6)
```

## Step 5: Intercept requests on a worker thread

Do privacy/security request handling in `shouldInterceptRequest`, **off the UI thread** (it is already called on a background thread; keep heavy work there and return a `WebResourceResponse?`):

- Inspect/validate or replace each resource request (tracker/malware blocking, HTTPS upgrade, surrogates).
- Keep `shouldOverrideUrlLoading` for **navigation gating only** (deciding whether to load a URL), not resource filtering.
- Never block the main thread; if a decision needs suspend work, model the interceptor as a `suspend` function invoked from a worker context.

## Step 6: Resilience: SSL errors and renderer crashes

- **SSL:** in `onReceivedSslError`, classify the error (expired / untrusted host / wrong host / generic) and show the user a typed warning. **Never** call `handler.proceed()` unconditionally.
- **RenderProcessGone:** override `onRenderProcessGone` to detect whether the renderer *crashed* vs was *killed* to reclaim memory, recover gracefully (recreate/reload), and log a metric. Without this, a renderer crash takes down the host activity.

## Step 7: Extensibility via plugins

For anything beyond a trivial WebView, make the `WebViewClient` an **orchestrator** that delegates to small, injected collaborators (a plugin point for JS injectors, an interceptor, cookie/login/consent handlers) rather than a monolith. This is how the reference app keeps a 30-responsibility client maintainable, see the reference.

## Verify

- Unit-test the interceptor's decisions (blocked vs allowed vs upgraded) with fake requests.
- For UI, drive the screen with an instrumentation/Maestro flow and confirm load, JS bridge round-trip, and error states (bad SSL, offline).

## Engine abstraction (later)

To support swapping the engine (stock WebView ↔ GeckoView), hide it behind a `concept-engine`-style interface and select by build flavor (Mozilla Android Components pattern). Build this only when multi-engine support is actually required.
