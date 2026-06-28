---
name: web-testing
description: "This skill should be used when writing or fixing the test for a web UI slice, \"write a test for this component\", \"test this form\", \"add a component test\", \"test the loading/empty/error states\", \"query by role not test id\", \"simulate a user click/type\", \"add an interaction test\", \"add an e2e test\", \"add an accessibility check to the test\", \"this test asserts on internals\", or reviewing a web test. Framework-agnostic and detect-first across React, Vue, Svelte, and Angular: test user-facing behavior with Testing Library, drive real interactions with user-event or Playwright, and gate accessibility with axe. This is the failable check that web-components and web-forms verify against."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Web testing

The failable check for a web slice. Test what a user sees and does, not how the component is wired inside. A test that asserts on state, class names, or call counts breaks on every refactor and proves nothing; a test that drives the UI like a user proves the slice works. If the test cannot fail, it is not a check.

## Step 1: Detect the runner and tools first
Never impose a stack. Read `package.json` and an existing test before writing:
- **Runner:** Vitest, Jest, Playwright, or Cypress. Match the one already wired (look at `scripts.test`, the config file, and existing `*.test` / `*.spec` files).
- **Component testing library:** the framework's Testing Library binding (`@testing-library/react`, `/vue`, `/svelte`, `angular-testing-library`). The queries and `user-event` are the same across all four; only `render` differs.
- **Interaction:** `@testing-library/user-event` for unit/component tests; Playwright (or Cypress) for end-to-end.
- **A11y:** `jest-axe` (Jest), `vitest-axe` (Vitest), or `@axe-core/playwright` (e2e). Pick the one that matches the runner.

If none exists, the lightest default for a Vite app is Vitest + the framework's Testing Library + `user-event` + `vitest-axe`; for a non-Vite app, Jest + `jest-axe`. Confirm before adding a dependency.

## Step 2: Test behavior and the contract, never internals
A component's contract is **props in, events out, and the states it renders.** Test exactly that:
- **Props in:** given props, the right thing renders. Assert on visible output, not on the prop being stored.
- **Events out:** a user action fires the callback / emit with the right payload. Spy on the handler the parent passes in, not on an internal method.
- **States:** cover **loading, empty, error,** and the populated success path. These are the bugs users actually hit; an untested error state is an untested feature.

Do not assert on component state, private methods, CSS class names, or render counts. If the only way to test something is to reach inside, the component boundary is wrong (see `web-components`, `software-design`).

## Step 3: Query the way a user finds things
Use the accessible query priority, the same in every framework:
1. `getByRole` (with `{ name }`) first: `getByRole('button', { name: /save/i })`. This is what a screen reader sees, so it doubles as an a11y signal.
2. Then `getByLabelText` (form fields), `getByPlaceholderText`, `getByText`.
3. `getByTestId` is the last resort, only when no accessible query fits.

If `getByRole` cannot find an element, that is usually a real accessibility bug (missing label, wrong element), not a reason to fall back to a test id. Fix the markup. Use `findBy*` for async appearance, `queryBy*` only to assert absence.

## Step 4: Drive real interactions
Simulate a user, do not call handlers directly:
- **Component / interaction:** `const user = userEvent.setup()` then `await user.click(...)`, `await user.type(...)`. `user-event` is async and dispatches the full event sequence (focus, keydown, input), so it catches bugs `fireEvent` misses.
- **End-to-end:** Playwright with the same role-based locators (`page.getByRole('button', { name: 'Save' })`), for real-browser flows that span pages, navigation, and network.
- Assert on the resulting user-visible change (text appears, button enables, error shows), then on the contract (the emitted event payload).

Use component/interaction tests for a single slice; reserve e2e for critical cross-page journeys. Do not e2e what a component test already covers.

## Step 5: Gate accessibility with an axe smoke check
Every component test renders something, so scan it:
- **Unit / component:** render, run axe, assert no violations.
  ```js
  import { axe } from 'vitest-axe' // or 'jest-axe'
  const { container } = render(<Card title="Hi" />)
  expect(await axe(container)).toHaveNoViolations()
  ```
- **E2e:** `new AxeBuilder({ page }).analyze()` and assert `violations` is empty.

axe catches roughly a third of real issues (contrast, names, roles, structure), so it is a smoke gate, not proof of accessibility. Keyboard reachability, focus order, and visible focus still need an explicit assertion or manual check (see `design-a11y`).

## Step 6: Confirm the test can fail
A green test that never fails is a liability. Before trusting it, break the component (or invert one assertion) and confirm the test goes red, then revert. The test passes only because the behavior is correct, not because the assertion is empty or the query matches nothing. Run the suite headless and keep it deterministic: no real network (mock the boundary), no arbitrary `sleep`, await the UI instead.

## References
- What this verifies: `web-components` (the component contract), `web-forms` (validation and error states). Shared / server state to mock at the boundary: `web-state`. E2e across rendered routes: `ssr-edge`. Performance budgets are a separate check: `web-performance`. Accessibility depth beyond the axe smoke gate: `design-a11y`, `adlc-design`. Where the boundary should sit: `software-design`.
