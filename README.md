# renovate-config

Org-wide [Renovate](https://docs.renovatebot.com/) shared presets for FlowMatrix-AI.

## Presets

### `default` — Org baseline

Safe for **any** repo type (Node, Python, Terraform, etc.). Provides only:

- Weekly schedule (before 7am Monday, Eastern)
- `dependencies` label on PRs
- Max 5 concurrent PRs
- Renovate's `config:recommended` base

**Usage:**
```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["local>FlowMatrix-AI/renovate-config"]
}
```

### `marketing-site` — Marketing fleet sites

Extends `default`. For repos consuming `@flowmatrix-ai/site-components`. Adds:

- GitHub Packages registry auth (`npm.pkg.github.com` via Renovate App token)
- Non-major npm updates: grouped, automerged
- Non-major GitHub Actions: grouped, automerged
- Tailwind packages: grouped, automerged
- `@flowmatrix-ai/*` internal packages: grouped, **not** automerged (manual review)
- Lock file maintenance: automerged

**Usage:**
```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["local>FlowMatrix-AI/renovate-config:marketing-site"]
}
```

## Auth for private packages

The `hostRules` entry in `marketing-site.json` lets the Renovate GitHub App use its installation token for `npm.pkg.github.com` lookups. If the App token lacks `packages:read`, add an encrypted PAT via [Renovate's encryption endpoint](https://app.renovatebot.com/encrypt).
