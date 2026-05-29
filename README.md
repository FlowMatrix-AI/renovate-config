# renovate-config

Org-wide [Renovate](https://docs.renovatebot.com/) shared preset for FlowMatrix-AI.

## Usage

In any repo's `renovate.json`:

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["local>FlowMatrix-AI/renovate-config"]
}
```

## What the preset provides

- **Schedule:** Weekly, before 7am Monday (America/New_York)
- **Registry auth:** `npm.pkg.github.com` configured via `hostRules` (uses Renovate App token)
- **Lock file maintenance:** automerged weekly
- **Package rules:**
  - Non-major npm updates: grouped, automerged
  - Non-major GitHub Actions: grouped, automerged
  - Tailwind packages: grouped, automerged
  - `@flowmatrix-ai/*` internal packages: grouped, **not** automerged (manual review)

## Auth for private packages

The `hostRules` entry for `npm.pkg.github.com` allows the Renovate GitHub App to use its installation token for package lookups. If this doesn't work (App token lacks `packages:read`), you'll need to add an encrypted PAT via [Renovate's encryption](https://app.renovatebot.com/encrypt).
