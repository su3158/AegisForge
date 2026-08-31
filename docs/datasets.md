# Datasets

Core AegisForge should include only minimal safe probes.

External datasets require:

- Explicit import.
- Source URL.
- License metadata.
- Revision pin.
- Content hashes.
- `.aegisforge/datasets.lock.json`.

Harmful datasets require isolated opt-in and must not run in default profiles.
