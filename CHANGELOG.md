# Changelog

## 0.2.0-alpha

- Added typed project, target, scope, scan, finding, evidence, secret, framework, and audit tables.
- Added Local Lite API workflows for scope confirmation, scan start/cancel, encrypted secrets, redacted evidence, raw reveal re-auth, framework coverage, and attack-chain candidates.
- Added in-process scan task registry, five-minute scan timeout, standard-probe consent gate, and rule-based attack-chain candidate generation.
- Added browser-flow YAML validation with allowlisted actions and Scope Guard checks for `goto`.
- Expanded React console into a project-centered workflow with target creation, scan wizard, evidence viewer, settings, coverage, attack chains, English/Japanese labels, dark mode, and README screenshots from the real UI.
- Added ASVS 5.0.0 L2 seed data files and source/license attribution.
- Added tests for API auth/CSRF, scope confirmation, encrypted secrets, raw evidence reveal, scan cancellation, browser-flow guard checks, evidence redaction, ASVS loading, and Playwright desktop/mobile smoke flows.

## 0.1.0-alpha

- Initial alpha skeleton planning.
- Docs, CI, Docker, and Compose scaffolding.
- Explicit alpha status, no-telemetry policy, framework sync policy, and dataset safety gates.
