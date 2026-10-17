# AGENTS.md

## Policy

Org engineering policy is authoritative and lives in
**[`FlowMatrix-AI/eng-governance`](https://github.com/FlowMatrix-AI/eng-governance)**.
Read it rather than inferring the rules from surrounding code:

| Where | What |
| --- | --- |
| [`DECISIONS.md`](https://github.com/FlowMatrix-AI/eng-governance/blob/main/DECISIONS.md) | Ratified engineering decisions, with the date each was locked |
| [`standards/`](https://github.com/FlowMatrix-AI/eng-governance/tree/main/standards) | Language, testing, security, dependencies, documentation |
| [`process/`](https://github.com/FlowMatrix-AI/eng-governance/tree/main/process) | Ownership, code review, pull requests, releases, design reviews |
| [`principles/`](https://github.com/FlowMatrix-AI/eng-governance/tree/main/principles) | Architecture and engineering principles |

Anything this file does not state follows those. What it *does* state
**overrides** org defaults for this repo — so say it here, rather than
restating policy that already lives there and will drift from it.

Cross-cutting technical documentation with no owning repo lives in
[`technical-docs`](https://github.com/FlowMatrix-AI/technical-docs).

## Project

The org's shared [Renovate](https://docs.renovatebot.com/) presets. Four
presets are published — `default`, `marketing-site`, `npmjs-scope`,
`site-npmjs` — and consumer repos extend them by name, e.g.
`"extends": ["local>FlowMatrix-AI/renovate-config"]`. Essentially the whole
fleet does: a `renovate.json` extending an org preset is part of the repo
baseline, and `eng-governance`'s `drift-audit.sh` flags any repo without one
(`renovate-not-org-preset`). Counted from the org's `renovate.json` files on
2026-09-28: `default` 57, `site-npmjs` 7, `marketing-site` 6, `npmjs-scope` 4.
**The repo is public** — deliberately, since `local>` presets are resolved by
the hosted bot — which is also why no check needing an org secret can live
here.

## Commands

```bash
# Validate every preset with the same renovate the hosted bot runs. The pin
# lives in .github/workflows/ci.yml as RENOVATE_VERSION (44.49.0 today).
npx --yes --package renovate@44.49.0 renovate-config-validator \
  --strict --no-global ./*.json

# What the validator cannot see.
python3 scripts/check-group-coherence.py    # ecosystem groups vs vulnerabilityAlerts
python3 scripts/check-preset-references.py  # every local> reference resolves to a file
```

## Architecture

Every root-level `*.json` is a preset. CI globs them rather than listing them,
because a hand-written list is how a new preset ships unvalidated.

| Preset | What it is |
| --- | --- |
| `default.json` | Org baseline, safe for any repo type. Monday schedule (America/New_York), `dependencies` label, `prConcurrentLimit: 5`, `prHourlyLimit: 0`, `minimumReleaseAge: "3 days"`, `internalChecksFilter: "strict"`, `osvVulnerabilityAlerts`, `constraints.npm`, the `@flowmatrix-ai` `npmrc`, TypeScript majors held behind dashboard approval. |
| `marketing-site.json` | Extends `default`. GitHub Packages scope auth, grouped + automerged non-major npm/Actions/Tailwind, `@flowmatrix-ai/*` grouped but **not** automerged, and a final rule forcing `automerge: false` on every `major`. |
| `npmjs-scope.json` | Single-purpose fragment that points the `@flowmatrix-ai` scope at `registry.npmjs.org`. Extended **alongside** another preset. |
| `site-npmjs.json` | `marketing-site` + `npmjs-scope`. |

`.github/workflows/ci.yml` runs the validator, both Python checks, and — for
each — a step that **proves the check can fail**, by feeding it a global-only
option, a dangling preset name, and a deleted published preset. `ok` aggregates
the jobs into the org's single required check.

`scripts/check-preset-references.py` carries a `PUBLISHED` list. That list, not
the filesystem, is the contract with consumers: a name in it must have a file.

## What NOT to do

- **Do not treat a merge here as a change to one repo.** There is no pin:
  `local>FlowMatrix-AI/renovate-config[:name]` resolves this repo's default
  branch on every bot run, so a merge changes dependency automation across the
  fleet within the next run — with no PR, no digest bump, and nothing touched
  in the consumer repos. Reason about the blast radius before merging, not
  after.
- **Do not rename or delete a preset file.** Consumers reference it by name from
  outside this repo, and a dangling `extends` does not error — Renovate falls
  back and those repos quietly stop getting updates.
  `renovate-config-validator` does not resolve `extends` and validates a
  nonexistent preset clean. Removing a name from `PUBLISHED` is the deliberate
  step that asserts consumers have been moved off it.
- **Do not bump `RENOVATE_VERSION` to npm's latest.** Ahead of the hosted bot is
  the dangerous direction: the validator then accepts config the bot rejects,
  so CI goes green over a preset that fails in production, estate-wide and
  silently. Behind is safe. Read the live bot version from `updatedInVer` in the
  base64 `renovate-debug` blob at the bottom of an **open** Renovate PR body —
  merged PRs freeze that field, and this repo's own merged PRs report 44.39.0.
  `eng-governance`'s `check-validator-pin.sh` watches this.
- **Do not group a package set in `packageRules` without repeating it under
  `vulnerabilityAlerts.packageRules`.** Renovate's built-in default for that
  block sets `groupName: null`, which overrides any grouping, so a grouped
  ecosystem is silently *un*-grouped for security updates and an advisory
  arrives as a partial bump that does not build. Three `astro` 6→7 `[security]`
  PRs sat red for a month each because of this, while the config validated
  clean the whole time. `check-group-coherence.py` is the only thing that
  catches it.
- **Do not add `npmjs-scope` to a repo that consumes any GitHub-Packages-only
  package.** npm maps a registry per **scope**, not per package, so one repo
  cannot draw one `@flowmatrix-ai` package from npmjs and another from GitHub
  Packages.
- **Do not treat `npmrc` as a lookup-only setting.** It is what Renovate hands
  `npm`/`pnpm` when it **regenerates a lockfile**, so it decides the `resolved`
  URLs that get committed; a `registryUrls` packageRule governs version lookup
  only. A repo that has dropped its `.npmrc` but still inherits the preset
  `npmrc` gets its lockfile rewritten back to GitHub Packages and the next
  install 401s. Seen twice on 2026-08-31.
- **Do not close a Renovate PR by hand to dismiss an update.** Closing tells the
  bot to drop that update permanently and nothing reports the gap afterwards.
  Deferring or suppressing an update belongs in a `packageRule` here — that is
  what this repo is for.
- **Do not rely on `automerge: true` alone.** Renovate uses GitHub *platform*
  automerge, which silently no-ops unless the repository setting "Allow
  auto-merge" is on; PRs just sit. `drift-audit` flags it as `auto-merge-off`.
- **Do not simplify the validator invocation.** `--package renovate` is
  required: the npm package literally named `renovate-config-validator` is a
  placeholder with no bin, so a bare `npx renovate-config-validator` passes
  vacuously. `--no-global` is required: given explicit paths the validator
  defaults to treating them as self-hosted *global* config, and a preset
  carrying a global-only option passes without it.
- **Do not add a workflow here that needs an org secret.** This repo is public
  and cannot reach one — that is why `check-validator-pin.sh` lives in
  `eng-governance` under `fleet-watch`'s token.
- **Do not add `hostRules` for `npm.pkg.github.com`.** An empty entry clobbered
  the Renovate App's auto-provisioned installation token and was removed.
