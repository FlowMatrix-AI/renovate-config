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
- **TypeScript majors held** behind Dependency-Dashboard approval. TS 7 is a
  native compiler that does not yet ship the programmatic API `astro check`
  loads, and it also breaks plain workspace typechecks and at least one app
  build. The hold keeps the major visible and one-click on the dashboard rather
  than silently dropping it. Minor and patch still flow normally.

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

### `npmjs-scope` — Point the `@flowmatrix-ai` scope at public npm

A single-purpose fragment, meant to be extended **alongside** another preset:

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "local>FlowMatrix-AI/renovate-config",
    "local>FlowMatrix-AI/renovate-config:npmjs-scope"
  ]
}
```

Use it in any repo whose `@flowmatrix-ai` dependencies are all on npmjs — since
2026-08-31 that is everything except `site-generator` and the eight
`checkout-*` packages.

**Why it is load-bearing.** `default.json` sets `npmrc` for the whole scope, and
that is not merely a lookup setting: it is what Renovate hands to `npm`/`pnpm`
when it **regenerates a lockfile**, so it decides the `resolved` URLs that get
committed. A repo that has dropped its `.npmrc` but still inherits that `npmrc`
gets its lockfile quietly rewritten back to GitHub Packages on the next lock
refresh, and the next install fails with `401 Unauthorized`. The `registryUrls`
packageRule does **not** prevent this — it governs version lookup only.

Observed twice on 2026-08-31: `site-marketfourseasons-main#66` and, after the
brand migration, `flowmatrixai-org#21`.

A repo consuming any GitHub-Packages-only package must **not** extend this: npm
maps a registry per **scope**, not per package.

### `site-npmjs` — Marketing sites migrated to public npm

`marketing-site` plus `npmjs-scope` — identical to `marketing-site` except that
the `@flowmatrix-ai` scope points at `registry.npmjs.org`.

Use this preset once a site's `package-lock.json` no longer contains any
`npm.pkg.github.com` URL. On `marketing-site`, lock file maintenance rewrites
those entries **back** to GitHub Packages — see [Auth for private
packages](#auth-for-private-packages) — and the next `npm ci` fails with
`401 Unauthorized`.

A site that still consumes a GitHub-Packages-only package (`site-generator`,
`checkout-*`) must stay on `marketing-site`: npm scopes a registry per **scope**,
not per package, so one repo cannot draw `@flowmatrix-ai/site-components` from
npmjs and `@flowmatrix-ai/checkout-ui` from GitHub Packages.

`@flowmatrix-ai/brand` used to be on that list. It went public on 2026-08-31, so
the three FlowMatrix-owned properties that depend on it — `site-flowmatrixai-main`,
`site-flowmatrixai-studio` and `flowmatrixai-org` — are no longer pinned to
GitHub Packages by it.

**Usage:**
```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["local>FlowMatrix-AI/renovate-config:site-npmjs"]
}
```

## Required repo setting: "Allow auto-merge"

The presets above set `automerge: true` on low-risk update types, but that only
takes effect if the **repository setting "Allow auto-merge" is enabled**.
Renovate uses GitHub *platform* automerge by default, which **silently no-ops**
when the repo setting is off — PRs then sit open until merged by hand (this is
exactly what stranded the sites fleet's pin/patch PRs).

Enable it per repo:
```sh
gh api -X PATCH repos/FlowMatrix-AI/<repo> -F allow_auto_merge=true
```
It is safe: auto-merge still fires only when the required checks (`ok` +
`gitleaks / gitleaks`) pass, branch protection is unchanged, and only renovate
PRs the presets mark `automerge: true` (non-major pins/digests/patches)
self-merge. The sites/marketing fleet (`tier=sites` + `site-platform`) has it
on; the drift-audit flags any fleet repo where it regresses (`auto-merge-off`).

## Auth for private packages

The `npmrc` entry in `default.json` points the `@flowmatrix-ai` scope at
`npm.pkg.github.com`; the Renovate GitHub App's auto-provisioned installation
token is used for lookups. (An empty `hostRules` entry was removed in
[`52d8074`](https://github.com/FlowMatrix-AI/renovate-config/commit/52d8074)
because it clobbered that auto-provisioned token.) If the App token lacks
`packages:read`, add an encrypted PAT via
[Renovate's encryption endpoint](https://app.renovatebot.com/encrypt) under a
`hostRules` entry.

**`npmrc` is not only a lookup setting.** It is also what Renovate hands to
`npm`/`pnpm` when it regenerates a lockfile, so it decides the `resolved` URLs
that get committed. The `registryUrls` packageRule for the three
`@flowmatrix-ai/site-*` packages governs lookup **only** and does not change
what lands in the lock. That is why a migrated site needs the `site-npmjs`
preset rather than the packageRule alone.
