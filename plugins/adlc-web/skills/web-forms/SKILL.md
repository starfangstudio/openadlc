---
name: web-forms
description: "This skill should be used when building or reviewing a web form, \"add a form\", \"validate this input\", \"wire up form validation\", \"share validation between client and server\", \"show accessible error messages\", \"why does my screen reader not announce errors\", \"move focus to the first error\", \"controlled vs uncontrolled input\", \"add Zod / Valibot / Yup validation\", or \"make this form keyboard accessible\". Framework-agnostic and detect-first across React, Vue, Svelte, and Angular: one schema validates both client and server, errors are accessible by default, and the failable check is a form test. Pairs with web-components (the inputs), web-state (form state), web-testing (the check), and design-a11y (the a11y bar)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Web forms

A form is a typed contract between the user and the server, validated by **one schema that runs in both places**, with errors a screen reader can announce. Accessibility is not a polish pass; it is part of the contract.

## Step 1: Detect the form approach first
Never impose a stack. Read `package.json` and an existing form before writing:
- **React / Next:** React Hook Form (most common) or Formik (legacy). Server Actions for the server half.
- **Vue / Nuxt:** VeeValidate or FormKit.
- **Svelte / SvelteKit:** Superforms (server + client), or native form actions.
- **Angular:** typed reactive forms (`FormGroup` / `FormControl`), or Signal Forms (`@angular/forms/signals`) in Angular 21+.

If none is installed and the form is simple, prefer native HTML form + a schema over adding a library. Match the project's existing forms; do not introduce a second form library.

## Step 2: Schema first, shared client and server
Write the validation **once** as a schema, then use it on both sides. Never copy-paste rules into two places; they drift, and the server is the only one you can trust.
- Pick the project's library: **Zod** (TypeScript default), **Valibot** (smallest bundle, tree-shakeable), or **Yup** (older, simpler, weaker types). All three implement **Standard Schema**, so most form libraries accept them through one adapter.
- Define the schema in a shared module both the form and the API import.
- The **client** validates for fast feedback. The **server re-validates the same schema** on submit; client validation is a UX convenience, not a security boundary (see `software-design`).
- Infer the type from the schema (`z.infer`) so the form values, the submit handler, and the API input share one source of truth.

```ts
// shared/contact.schema.ts  (imported by both the form and the server)
import { z } from "zod";
export const ContactSchema = z.object({
  email: z.string().email("Enter a valid email"),
  message: z.string().min(10, "At least 10 characters"),
});
export type Contact = z.infer<typeof ContactSchema>;
```

## Step 3: Wire it idiomatically (per framework)
Connect the schema through the framework's resolver, not by hand-rolling validation.
- **React Hook Form:** `useForm({ resolver: standardSchemaResolver(ContactSchema) })` from `@hookform/resolvers/standard-schema` (or the library-specific `zodResolver` from `@hookform/resolvers/zod`).
- **VeeValidate:** wrap the schema with `toTypedSchema(ContactSchema)` from `@vee-validate/zod` and pass it as `validation-schema`; values and submitted values become typed.
- **Superforms:** pass the schema through its adapter (`zod(ContactSchema)`) in the load function; it merges server and client validation and coerces `FormData` to typed values.
- **Angular reactive forms:** build the `FormGroup` with `Validators` and custom `ValidatorFn`s; for cross-field rules use a group-level validator. (Signal Forms express the same rules declaratively as a schema.)

## Step 4: Controlled vs uncontrolled, and native validation
Decide who owns the input value and lean on the platform:
- **Uncontrolled (default, cheaper):** the DOM holds the value; read it on submit. React Hook Form's `register` is uncontrolled by design and re-renders less.
- **Controlled:** state owns the value, needed for live formatting, dependent fields, or masking. Costs a render per keystroke; use it only when you need it (see `web-state`).
- **Native HTML validation + progressive enhancement:** use real `<form>`, `<input type="email" required>`, and a submit button so the form works before JS loads. Let native constraints catch the obvious cases, then layer the schema for richer rules and consistent messages. Do not block submit on a `div` with a click handler; use a `<button type="submit">`.

## Step 5: Accessible errors are mandatory
An error a screen reader cannot announce is a bug, not a nuance. Every field error needs all four:
- **Label association:** every control has a real `<label for>` (or wraps the input). Placeholder text is not a label.
- **`aria-describedby`:** point the input at its error element's `id`, and set `aria-invalid="true"` when invalid, so the error is read with the field.
- **`aria-live` for async / submit errors:** put server or post-submit errors in an `aria-live="polite"` region (or `role="alert"`) so they are announced without moving focus. Do not double up `aria-live` on an error already wired through `aria-describedby`; it gets announced twice.
- **Move focus to the first invalid field on submit:** after a failed submit, send focus to the first error (or an error summary linking to each field). This is the single highest-impact fix for keyboard and screen-reader users.

```html
<label for="email">Email</label>
<input id="email" type="email" aria-describedby="email-err" aria-invalid="true" />
<p id="email-err" role="alert">Enter a valid email</p>
```

Errors must be text, not color alone; keep focus visible; keep messages specific ("Enter a valid email", not "Invalid"). See `design-a11y`.

## Step 6: Verify
The failable check is a form test (see `web-testing`):
- A valid submit calls the handler with the typed, parsed values.
- An invalid field blocks submit, renders its message, and sets `aria-invalid`.
- The error is linked via `aria-describedby` and focus lands on the first invalid field.
- The server rejects the same bad input the client rejected (the shared schema actually runs server-side).

A form with no test for its error path is not done.

## References
- The inputs as components: `web-components`. Form and shared state: `web-state`. The check: `web-testing`. Server / form-action boundary and re-validation: `ssr-edge`. Label, error, focus, contrast bar: `design-a11y`, `adlc-design`. Schema as a trust boundary and domain rules: `software-design`. Submit cost and large-form rendering: `web-performance`.
