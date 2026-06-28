<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `oss-license-scan` skill. Load on demand; do not load independently.

---

## Scanner commands (Step 1)

### Gradle (Android)

Add the `jk1/Gradle-License-Report` plugin to `build.gradle`, then:

```bash
./gradlew generateLicenseReport
# Output: build/reports/licenses/
```

### npm / Node / UPM

```bash
npx license-checker-rseidelsohn --production \
  --csv --out license-report.csv
```

### SPM (iOS) via ORT

```bash
ort analyze -i . -o ort-result/ --package-managers SPM
ort report -i ort-result/analyzer-result.yml \
  -o ort-report/ -f SPDX,CycloneDX
```

### Multi-ecosystem / SBOM-grade audit via LicenseFinder

```bash
license_finder --decisions_file decisions.yml report \
  --format csv > license-report.csv
```

---

## SBOM generation commands (Step 4)

```bash
# ORT (preferred):
ort report -i ort-result/analyzer-result.yml \
  -o sbom/ -f SPDX,CycloneDX

# license_finder:
license_finder report --format spdx_rdf > sbom.spdx
```
