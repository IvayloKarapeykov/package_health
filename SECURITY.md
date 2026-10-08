# Security

## Reporting a vulnerability

Please don't open a public issue. Report it privately through
[GitHub's security advisories](https://github.com/IvayloKarapeykov/package_health/security/advisories/new)
instead, with the steps to reproduce it and what an attacker could do with it.

You'll get a reply within a few days. Once it's fixed, the advisory is published with credit to you,
unless you'd rather stay anonymous.

## What's in scope

- The backend API and the MCP endpoint, including the public server at
  `https://api.vet.ivaylokarapeykov.com`
- The web app at `https://vet.ivaylokarapeykov.com`
- How the GitHub and OpenRouter keys people bring are handled
- The code in this repository

Problems in the registries, GitHub or OSV.dev themselves are out of scope; please report those to
their owners. Hitting the rate limits on the public server is expected, not a vulnerability.

## Supported versions

Fixes go into the latest release and the public server. Older releases don't get patches.
