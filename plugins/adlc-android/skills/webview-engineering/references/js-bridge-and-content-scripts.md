<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# JS ↔ native bridge & content scripts (reference)

How a privacy-focused Android browser structures a secure, multi-feature JavaScript bridge. Read alongside `webview-architecture.md`. Source: `js-messaging/js-messaging-api/`, `autoconsent/`, `content-scope-scripts/`.

## Contents
- The bridge contract (`JsMessaging`)
- Two transports: legacy interface vs WebViewCompat
- Security model (secret + allowed domains)
- The plugin model (document-start injection)
- Feature example: Autoconsent
- Applying it

## The bridge contract: `JsMessaging`
A single interface defines the contract so every feature speaks the same protocol:
```
interface JsMessaging {
    fun register(webView: WebView, jsMessageCallback: JsMessageCallback?)   // wire up the bridge
    @JavascriptInterface fun process(message: String, secret: String)        // JS → native entry
    fun onResponse(response: JsCallbackData)                                 // native → JS reply
    fun sendSubscriptionEvent(subscriptionEventData: SubscriptionEventData)  // native → JS push
    val context: String        // bridge/context name
    val callbackName: String   // JS-side callback name
    val secret: String         // shared token validating each message
    val allowedDomains: List<String>  // origins allowed to receive this interface
}
abstract class JsMessageCallback { abstract fun process(featureName, method, id, data: JSONObject?) }
```
Messages are routed by `featureName` + `method`, with an `id` correlating a reply. A `JsMessageHandler` per feature processes a `JsMessage` and optionally returns a `JsRequestResponse`; `JsMessageHelper` sends responses/subscription events back into the page.

## Two transports
- **Legacy:** `@JavascriptInterface process(message, secret)` injected via `addJavascriptInterface`, guarded by the secret.
- **Modern:** `WebViewCompatMessaging` / `WebMessagingPlugin` use AndroidX `WebViewCompat` `WebMessageListener` (origin-scoped `postMessage`). **Prefer this** for new code, it scopes the bridge to specific origins and avoids the reflection surface of `addJavascriptInterface`.

## Security model
- **Secret token:** every inbound `process(message, secret)` call must present the expected `secret`; the page receives it only via trusted injected code, so arbitrary in-page script can't drive the bridge.
- **Allowed domains:** `allowedDomains` restricts which origins the interface is exposed to, never expose a native bridge to all frames/origins.
- **Document-start injection:** `AddDocumentStartJavaScriptPlugin` injects the client JS before page scripts run, so protections are in place before untrusted code executes.

## The plugin model
The bridge is a plugin point, not a monolith: each feature contributes a `JsMessageHandler` (and optionally a document-start script + a subscription event source). Adding a feature = adding a handler, not editing the WebView. This is why one WebView can host autofill, autoconsent, content-scope protections, DuckPlayer, etc., independently.

## Feature example: Autoconsent (CMP auto opt-out)
```
interface Autoconsent {
    fun injectAutoconsent(webView: WebView, url: String)        // inject the feature JS
    fun addJsInterface(webView: WebView, callback: AutoconsentCallback)  // wire the bridge
    fun setAutoconsentOptOut(webView: WebView); fun setAutoconsentOptIn()
    fun isAutoconsentEnabled(): Boolean; fun changeSetting(enabled: Boolean)
    fun firstPopUpHandled()
}
```
Pattern to copy: a feature exposes a tiny `-api` interface (`inject…`, `addJsInterface(callback)`, settings), keeps its JS in a shared JS project (`content-scope-scripts`), and talks to native through the common bridge, no feature-specific WebView surgery.

## Applying it to a new app
1. Define one bridge contract (message in, response out, subscription push) with a **secret** + **allowedDomains**.
2. Use `WebMessageListener` as the transport.
3. Inject feature JS at **document start**.
4. Make each feature a handler/plugin keyed by `featureName`, not a WebView edit.
5. Keep shared JS in one place and version it with the app.
