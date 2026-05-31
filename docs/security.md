# Security Checks

CareShield uses public-repo-friendly security checks by default and leaves
enterprise scanners as documented integration points.

## Current Checks

```bash
make security
```

This runs `pip-audit --strict` against the Python environment. CI also runs the
same dependency audit before building the container image.

The CI pipeline also builds the Chainguard-based container and smoke-tests that
the app imports inside the image.

## SonarQube / SonarCloud

SonarQube is useful for code quality, duplication, maintainability, and security
hotspots. It normally requires:

- a SonarQube server or SonarCloud organization
- a project key
- a token stored as a protected GitHub Actions credential

Recommended future setup:

```yaml
- uses: SonarSource/sonarqube-scan-action@v6
  env:
    SONAR_TOKEN: ${{ vars.SONAR_TOKEN }}
```

Do not add this as a mandatory CI step until the token and project are ready.

## Twistlock / Prisma Cloud

Twistlock is now Prisma Cloud Compute. It is usually enterprise-managed and
requires:

- Prisma Cloud console URL
- access credentials
- scanner image or CI plugin approved by the organization

Recommended future setup:

1. Build the image in CI.
2. Scan the image with the Prisma Cloud scanner.
3. Fail on critical/high vulnerabilities according to policy.
4. Publish the scan report as a CI artifact.

## Trivy Alternative

For a public open-source style equivalent, add Trivy image scanning after the
container build. This is the closest open tool to the container vulnerability
part of a Twistlock-style gate.

Recommended future setup:

```yaml
- uses: aquasecurity/trivy-action@master
  with:
    image-ref: careshield-knowledge-assistant
    severity: HIGH,CRITICAL
    ignore-unfixed: true
    exit-code: "1"
```

This is not enabled by default here because scanner image/network availability
can make quick learning CI noisy.
