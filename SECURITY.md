# Security Policy

## Supported Versions

`0.1.0-alpha` is an in-development skeleton. Security reports are welcome, but the release is not production-ready.

## Reporting a Vulnerability

Do not open public issues for vulnerabilities. Use GitHub private vulnerability reporting when available, or contact the maintainer listed in the repository metadata.

Please include:

- Affected version or commit.
- Reproduction steps.
- Impact.
- Whether the issue involves Scope Guard, authentication, secrets, evidence, or report leakage.

## Severity Guidance

Treat these as Critical unless proven otherwise:

- Scope Guard bypass.
- Authentication bypass.
- Raw secret exposure.
- Cross-project evidence or secret access.
- Unapproved external exfiltration.
- Harmful dataset execution without explicit opt-in.

## Dependency Security

CI is expected to fail on high or critical dependency audit findings once package files exist. SBOM artifacts should be attached to CI runs.

## Telemetry

AegisForge must not send usage telemetry to project maintainers by default.
