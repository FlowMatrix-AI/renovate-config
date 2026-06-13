# renovate-config

Org-wide [Renovate](https://docs.renovatebot.com/) shared presets for FlowMatrix-AI.

## Presets

### `default` — Org baseline

Safe for **any** repo type (Node, Python, Terraform, etc.). Provides:

- Weekly schedule (before 7am Monday, Eastern)
- `dependencies` label on PRs
- Max 5 concurrent PRs
- Renovate's `config:recommended` base
- **Supply-chain cooldown:** `minimumReleaseAge: "3 days"` — a freshly
  published version is not eligible until it has been public for 3 days,
  reducing exposure to compromised/yanked releases. Applies to all managers
  (npm, GitHub Actions, etc.).
- **`internalChecksFilter: "strict"`** — holds branches/PRs until internal
  checks (including the release-age cooldown) pass, so automerge can never
  fire before the cooldown elapses.
- **`osvVulnerabilityAlerts: true`** — vulnerability alerts from the OSV
  database in addition to GitHub advisories.

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
- Tailwind packages: grouped, automerged (non-major only — see guard below)
- `@flowmatrix-ai/*` internal packages: grouped, **not** automerged (manual review)
- Lock file maintenance: automerged
- **Major-update safety guard:** a final `packageRule` forces `automerge: false`
  for every `major` update, so no group rule can ever automerge a breaking
  version. Combined with the baseline cooldown, automerges are both delayed and
  non-major-only.

**Usage:**
```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["local>FlowMatrix-AI/renovate-config:marketing-site"]
}
```

## Auth for private packages

The `npmrc` entry in `marketing-site.json` points the `@flowmatrix-ai` scope at
`npm.pkg.github.com`; the Renovate GitHub App's auto-provisioned installation
token is used for lookups. (An empty `hostRules` entry was removed in
[`52d8074`](https://github.com/FlowMatrix-AI/renovate-config/commit/52d8074)
because it clobbered that auto-provisioned token.) If the App token lacks
`packages:read`, add an encrypted PAT via
[Renovate's encryption endpoint](https://app.renovatebot.com/encrypt) under a
`hostRules` entry.
