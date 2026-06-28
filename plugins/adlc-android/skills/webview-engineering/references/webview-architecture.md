<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Android WebView architecture (reference)

Concrete, class-by-class patterns read from a privacy-focused browser's Android source (`app/src/main/java/.../browser/`). Use as a worked example of a production, privacy-hardened, stock-`WebView` browser.

## Contents
- Custom WebView subclass
- WebViewClient as orchestrator
- Request interception (the privacy/security core)
- JS bridge
- Custom Tabs
- Supporting injectors to study

## Custom WebView subclass
- Extends `WebView` and implements `NestedScrollingChild3` (toolbar hide-on-scroll in a `CoordinatorLayout`).
- DI: `@InjectWith(ViewScope::class)`, injected in `onAttachedToWindow()` via `AndroidSupportInjection.inject(this)`.
- **Crash safety:** an `isDestroyed` flag guards `destroy()`, `stopLoading()`, `onPause()` so a torn-down WebView never receives calls. An `isSafeWebViewEnabled` flag gates the behavior.
- **JS bridge:** origin-scoped `WebMessageListener` (not `addJavascriptInterface`). Full contract is single-sourced in [js-bridge-and-content-scripts.md](js-bridge-and-content-scripts.md).
- Hooks system autofill (`AutofillValue`, `InputConnection`) and disables typing personalisation.

## WebViewClient as orchestrator: `BrowserWebViewClient`
A single `WebViewClient` that **delegates to ~30 injected collaborators** rather than doing everything inline. Notable responsibilities and the collaborators they map to:
- **Typed SSL errors**: `SSLErrorType` (EXPIRED / UNTRUSTED_HOST / WRONG_HOST / GENERIC) + a `TrustedCertificateStore`; never blanket-proceeds.
- **Renderer crash recovery**: `onRenderProcessGone` distinguishes crash vs killed, recovers, and fires `WEB_RENDERER_GONE_CRASH` / `WEB_RENDERER_GONE_KILLED` pixels.
- **HTTP basic auth**: `BasicAuthenticationRequest` / `WebViewHttpAuthStore`.
- **JS injection plugin point**: `PluginPoint<JsInjectorPlugin>` (print, blob conversion, email, autofill, content-scope experiments).
- **Login detection**: `DOMLoginDetector` emitting `WebNavigationEvent`s.
- **Consent / autofill / cookies**: `Autoconsent`, `BrowserAutofill`, `ThirdPartyCookieManager`.
- **Analytics**: `PageLoadWideEvent`, `PageLoadedHandler`, `PagePaintedHandler` (page-load journey as a wide event).

Takeaway: keep the client thin; push each concern into an injected, independently testable collaborator.

## Request interception: `WebViewRequestInterceptor` (`RequestInterceptor`)
- Signature: `@WorkerThread suspend fun shouldIntercept(request: WebResourceRequest, webView, documentUri): WebResourceResponse?`: runs **off the UI thread**.
- Pipeline: malicious-site blocking (`MaliciousSiteBlockerWebViewIntegration`), ad-click (`AdClickManager`), tracker detection/blocking (`TrackerDetector`, `WebTrackersBlockedDao`) + surrogates (`ResourceSurrogates`), HTTPS upgrade (`HttpsUpgrader`), GPC (`Gpc`), request filtering/blocklist (`RequestFilterer`, `RequestBlocklist`), CNAME-cloaking detection (`CloakedCnameDetector`), trusted-sites/allowlist (`TrustedSites`, `UserAllowListRepository`), an embedded video player.
- This is the security/privacy heart of the browser, and it is deliberately separated from the client.

## JS messaging: content scripts
The bridge contract (secret token, allowed origins, document-start injection, transports) is single-sourced in **[js-bridge-and-content-scripts.md](js-bridge-and-content-scripts.md)**: not repeated here. Injectors seen at this layer: `EmailInjectorJs`, `BlobConverterInjector`, `PrintInjector`, `ClipboardImageInjector`, `BrowserServiceWorkerClient`, `InlineBrowserAutofill`.

## Custom Tabs: `custom-tabs/`
- `CustomTabDetector` / `RealCustomTabDetector` decide when a URL should open in a custom tab.
- A `CustomTabService` implementation backs the Custom Tabs service.

## To study next (when extending this reference)
`autoconsent` (cookie-consent automation), `autofill` (InlineBrowserAutofill, email protection), and the `content-scope-scripts` JS↔native message contract.
</content>
