# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in CVision, please report it privately by emailing the maintainers at **security@cvision.app** (placeholder — replace with actual address).

Please do **not** open a public GitHub issue for security vulnerabilities.

## What to include

- A brief description of the vulnerability
- Steps to reproduce
- Affected versions (if known)
- Any potential mitigations you've identified

## Response timeline

- We will acknowledge receipt within **48 hours**
- We aim to triage and confirm within **5 business days**
- A fix will be released as soon as practical, depending on severity

## Scope

The following are in scope:

- The Python backend (`api.py`, agents, auth, config)
- The frontend (`frontend/`)
- CI/CD pipelines (`.github/workflows/`)

Out of scope:

- Third-party dependencies (report those to their respective maintainers)
- LinkedIn's own platform and scraping policy

## Supported versions

Only the latest release on the `main` branch receives security patches.
