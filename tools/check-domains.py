#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0
"""Domain-detector determinism check (dev-time test, not pack runtime).

Proves the marker table documented in standard/domains.md yields the expected
domain set for each fixture repo under tools/test/domains/fixtures/, including
multi-domain fixtures (fx-multi -> {web, backend-cloud}; fx-monetization-android
-> {android, monetization}).

This is a dev-time fixture test (like check-packs.py), not something a pack
ships or a command runs at plan time: the command follows the declarative
procedure in standard/domains.md directly, it does not shell out to this
script. This script only proves that procedure is correct and deterministic.

Usage: python3 tools/check-domains.py
Exit 0 pass, 1 fail (any fixture's actual set != its expected set), 2 no
fixtures found (fail-closed).
"""
import os
import sys
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES_DIR = os.path.join(ROOT, "tools", "test", "domains", "fixtures")

# The marker table from standard/domains.md section 2, one detector function
# per technical domain. Each returns True when at least one marker condition
# matches inside the given fixture directory.

WEB_FRAMEWORKS = ("react", "vue", "svelte", "next", "nuxt", "angular", "vite", "remix", "astro")
BACKEND_JS = ("express", "fastify", "nest", "koa", "hapi")
BACKEND_PY = ("fastapi", "django", "flask")
BACKEND_GO = ("gin", "echo", "fiber")
ML_DEPS = ("torch", "tensorflow", "transformers", "langchain", "openai", "anthropic")
IOS_BILLING = ("StoreKit", "RevenueCat", "purchases-ios")
CROSS_PLATFORM_IAP = ("react-native-iap", "cordova-plugin-purchase", "expo-in-app-purchases")


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _glob(d, pattern):
    return glob.glob(os.path.join(d, "**", pattern), recursive=True)


def is_web(d):
    pkg = _read(os.path.join(d, "package.json"))
    return any(dep in pkg for dep in WEB_FRAMEWORKS)


def is_backend(d):
    pkg = _read(os.path.join(d, "package.json"))
    if any(dep in pkg for dep in BACKEND_JS):
        return True
    py = _read(os.path.join(d, "pyproject.toml")) + _read(os.path.join(d, "requirements.txt"))
    if any(dep in py for dep in BACKEND_PY):
        return True
    go = _read(os.path.join(d, "go.mod"))
    if any(dep in go for dep in BACKEND_GO):
        return True
    build = (
        _read(os.path.join(d, "pom.xml"))
        + _read(os.path.join(d, "build.gradle"))
        + _read(os.path.join(d, "build.gradle.kts"))
    )
    if "spring" in build:
        return True
    if _glob(d, "openapi.yaml") or _glob(d, "openapi.json") or _glob(d, "*.openapi.*"):
        return True
    return False


def is_backend_cloud(d):
    if os.path.isfile(os.path.join(d, "Dockerfile")):
        return True
    if _glob(d, "*.tf") or _glob(d, "*.tfvars"):
        return True
    if os.path.isdir(os.path.join(d, "k8s")) or os.path.isfile(os.path.join(d, "kustomization.yaml")):
        return True
    return bool(_glob(d, "Chart.yaml"))


def is_android(d):
    build = _read(os.path.join(d, "build.gradle")) + _read(os.path.join(d, "build.gradle.kts"))
    if "kotlin" in build or "android" in build:
        return True
    return bool(_glob(d, "AndroidManifest.xml"))


def is_ios(d):
    if os.path.isfile(os.path.join(d, "Package.swift")):
        return True
    return bool(_glob(d, "*.xcodeproj")) or bool(_glob(d, "*.xcworkspace"))


def is_desktop(d):
    if os.path.isfile(os.path.join(d, "src-tauri", "tauri.conf.json")):
        return True
    pkg = _read(os.path.join(d, "package.json"))
    return "electron" in pkg


def is_database(d):
    if os.path.isdir(os.path.join(d, "migrations")):
        return True
    if _glob(d, "*.sql"):
        return True
    if os.path.isfile(os.path.join(d, "schema.prisma")):
        return True
    return os.path.isfile(os.path.join(d, "alembic.ini"))


def is_ai(d):
    manifests = ("package.json", "pyproject.toml", "requirements.txt")
    text = "".join(_read(os.path.join(d, m)) for m in manifests)
    if any(dep in text for dep in ML_DEPS):
        return True
    return os.path.isdir(os.path.join(d, "evals"))


def is_unity(d):
    if not os.path.isdir(os.path.join(d, "ProjectSettings")):
        return False
    return bool(_glob(d, "*.unity")) or os.path.isdir(os.path.join(d, "Assets"))


def is_ops(d):
    if _glob(d, os.path.join(".github", "workflows", "*.yml")) or _glob(d, os.path.join(".github", "workflows", "*.yaml")):
        return True
    if os.path.isfile(os.path.join(d, ".gitlab-ci.yml")):
        return True
    deploy_manifests = ("Procfile", "fly.toml", "render.yaml", "vercel.json", "netlify.toml")
    return any(os.path.isfile(os.path.join(d, m)) for m in deploy_manifests)


def is_monetization(d):
    build = _read(os.path.join(d, "build.gradle")) + _read(os.path.join(d, "build.gradle.kts"))
    if "com.android.billingclient" in build:
        return True
    swift = _read(os.path.join(d, "Package.swift")) + _read(os.path.join(d, "Podfile"))
    if any(dep in swift for dep in IOS_BILLING):
        return True
    pkg = _read(os.path.join(d, "package.json"))
    return any(dep in pkg for dep in CROSS_PLATFORM_IAP)


DETECTORS = {
    "web": is_web,
    "backend": is_backend,
    "backend-cloud": is_backend_cloud,
    "android": is_android,
    "ios": is_ios,
    "desktop": is_desktop,
    "database": is_database,
    "ai": is_ai,
    "unity": is_unity,
    "ops": is_ops,
    "monetization": is_monetization,
}

# Expected domain set per fixture, per standard/domains.md's marker table.
EXPECTED = {
    "fx-web": {"web"},
    "fx-backend": {"backend"},
    "fx-backend-cloud": {"backend-cloud"},
    "fx-android": {"android"},
    "fx-ios": {"ios"},
    "fx-desktop": {"desktop"},
    "fx-database": {"database"},
    "fx-ai": {"ai"},
    "fx-unity": {"unity"},
    "fx-ops": {"ops"},
    "fx-monetization-android": {"android", "monetization"},
    "fx-monetization-ios": {"ios", "monetization"},
    "fx-multi": {"web", "backend-cloud"},
    "fx-empty": set(),
    # Unity boundary fixtures: pin `ProjectSettings AND (*.unity OR Assets)`.
    "fx-assets-only": set(),       # bare Assets/ (no ProjectSettings) must NOT match unity
    "fx-unity-assets": {"unity"},  # ProjectSettings + Assets, no scene, DOES match
}


def detect(fixture_dir):
    return {name for name, fn in DETECTORS.items() if fn(fixture_dir)}


def main():
    if not os.path.isdir(FIXTURES_DIR):
        print(f"FAIL-CLOSED: fixtures dir not found: {FIXTURES_DIR}")
        return 2

    fixtures = sorted(
        d for d in os.listdir(FIXTURES_DIR) if os.path.isdir(os.path.join(FIXTURES_DIR, d))
    )
    if not fixtures:
        print("FAIL-CLOSED: zero fixtures found")
        return 2

    missing_expected = [f for f in fixtures if f not in EXPECTED]
    if missing_expected:
        print(f"FAIL: fixture(s) with no EXPECTED entry: {missing_expected}")
        return 1

    failures = []
    for name in fixtures:
        actual = detect(os.path.join(FIXTURES_DIR, name))
        expected = EXPECTED[name]
        if actual != expected:
            failures.append((name, sorted(expected), sorted(actual)))

    # Determinism: detection depends ONLY on the repo's files, never on the
    # caller's working directory (the detectors take an absolute path). Prove
    # CWD-independence by sniffing each fixture from a different working dir and
    # asserting the set is unchanged. (This is a real property; comparing
    # detect(d) to itself would be a tautology.)
    origin_cwd = os.getcwd()
    baseline = {name: detect(os.path.join(FIXTURES_DIR, name)) for name in fixtures}
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        for name in fixtures:
            if detect(os.path.join(FIXTURES_DIR, name)) != baseline[name]:
                failures.append((name, "stable", "varies by caller CWD"))
    finally:
        os.chdir(origin_cwd)

    print(f"fixtures checked: {len(fixtures)}")
    for name in fixtures:
        print(f"  {name}: expected={sorted(EXPECTED[name])} actual={sorted(detect(os.path.join(FIXTURES_DIR, name)))}")

    if failures:
        print(f"\nFAIL ({len(failures)}):")
        for name, expected, actual in failures:
            print(f"  - {name}: expected {expected}, got {actual}")
        return 1

    print("\nRESULT: PASS (marker table matches every fixture's expected domain set)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
