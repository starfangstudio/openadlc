<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Android naming

Consistent names make the DI graph and module boundaries legible.

## Modules
- Feature split: `<feature>-api` / `<feature>-impl` (kebab-case). API holds interfaces + data classes only.

## Types
- Interfaces are named for the capability (e.g. `Autoconsent`, `CustomTabDetector`); the production implementation is prefixed **`Real`** (`RealAutoconsent`) and bound with `@ContributesBinding`. Fakes/tests use `Fake`/`Test` prefixes.
- ViewModels end `ViewModel`; UI state classes end `UiState`/`State`; user-intent sealed types end `Event`/`Intent`.
- One top-level Kotlin declaration per file, file named after it.

## Resources
- String files per feature: `strings-<feature>.xml` (never a shared `strings.xml`).
- Prefix resource ids/keys by feature to avoid cross-module collisions.

## Tests
- Method names describe behavior: `methodUnderTest_condition_expectedResult`, or backtick-quoted sentences. One behavior per test.

## Telemetry
- Event/pixel names: clear and descriptive, word-separated consistently, **no PII**, no URLs/domains, bounded enums over free-form strings. (See a telemetry rule if the project has one.)
