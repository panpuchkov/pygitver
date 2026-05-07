# SemVer bump rules derived from commit types

- Status: Accepted
- Date: 2026-05-06

## Context and Problem Statement

Given a range of commits between two refs, the tool must decide whether the
next release is a major, minor, or patch bump. The decision must be
deterministic — the same commit range must always yield the same answer —
and it must be derivable from data already in the commit messages so that
no separate "release notes" input is needed.

ADR-0001 establishes Conventional Commits as the input format. This ADR
defines the mapping from commit *types* to SemVer *components*, and the
precedence rules when a range contains commits of mixed types.

## Decision Drivers

- Determinism: the same range yields the same bump every time.
- Predictability: contributors should be able to look at one commit and
  know what bump it implies, without reading the rest of the range.
- Conservatism: when in doubt, bump *something* (default to patch) rather
  than nothing — silence is the worst outcome because it suggests a stable
  release with no real movement.
- Honor SemVer's contract: breaking changes are major; backwards-compatible
  features are minor; everything else is patch.

## Considered Options

- Per-commit-type mapping with major-wins precedence (this ADR).
- Per-commit-type mapping with strict-no-bump rules (i.e., `chore` produces
  no bump at all).
- Manual override per release via a flag or commit footer.

## Decision Outcome

Chosen: **per-commit-type mapping with major-wins precedence**.

Mapping rules, applied to each commit in the range:

| Commit signal                                              | Triggers      |
| ---------------------------------------------------------- | ------------- |
| `<type>!: ...` (type with `!`)                             | major         |
| `<type>(scope)!: ...`                                      | major         |
| `BREAKING CHANGE` header or `... breaking change: ...` body| major         |
| `feat:`, `feat(scope):`                                    | minor         |
| `fix:`, `fix(scope):`                                      | patch         |
| `docs:`, `docs(scope):`                                    | patch         |
| `deprecated:`, `deprecated(scope):`                        | recorded only |
| Any other recognized type (`build`, `chore`, `ci`, `style`, `refactor`, `perf`, `test`) | patch |
| Non-conventional (matches none of the above)               | patch         |

Multiple signals in one range are accumulated independently. The bump
*decision* applies the highest-priority component that fired, in this
strict order: **major > minor > patch**. A range containing one `feat` and
one `fix!` produces a major bump, not a minor one.

Edge cases:

- An empty range (no commits) produces no bump signal. When the current
  version is a real tag (e.g., `v1.2.3`), the bumped value equals the
  current value — the tool emits the unchanged version rather than
  failing. Operators are expected to detect "nothing changed" by
  comparing `--curr-ver` and `--next-ver` themselves; see ADR-0004 for
  the CLI behavior.
- The "no prior tag" case: if `version_current()` returns the sentinel
  `v0.0.0`, the bump is computed against the full commit history from
  the first commit to `HEAD`, and the resulting version starts at
  `v0.0.1`. A post-bump fallback enforces `0.0.0 → 0.0.1` so that the
  first published version is never `0.0.0`. This makes the tool usable
  on a fresh repository that has commits but has not been tagged yet.
- `deprecated:` commits are surfaced in the changelog under their own
  group but do not by themselves drive a bump. A deprecation is typically
  introduced alongside a `feat:` (minor) or as part of a breaking change
  (major); leaving it neutral avoids double-counting.

### Consequences

- Good: a single regex pass over the commit log determines both the
  changelog grouping and the bump rule set.
- Good: contributors see, per commit, what bump it implies — the rule is
  on the commit, not in a separate config.
- Good: major-wins precedence prevents accidental "shipped a feat with a
  hidden breaking change as a minor" releases.
- Bad: types we treat as patch (`build`, `chore`, `ci`, `refactor`, etc.)
  produce visible version churn even when they do not change runtime
  behavior. Acceptable: the cost of one wasted patch number is much lower
  than the cost of a missed bump.
- Bad: the mapping is fixed in code; changing it is itself a breaking
  change for downstream consumers, since their CI may have hard-coded
  expectations. Any change must come via a new ADR superseding this one.

## Pros and Cons of the Options

### Per-commit-type mapping with major-wins precedence

- Good: deterministic; reproducible from history alone.
- Good: matches the SemVer mental model.
- Bad: noisy patch bumps (see Consequences).

### Per-commit-type mapping with strict no-bump rules

- Good: quieter — `chore`-only ranges produce no release.
- Bad: if a `chore`-only range goes out unreleased, it can hide a real
  behavior change a contributor mis-typed. The current rule's small
  noise is the price of catching that mistake.
- Bad: introduces a "no bump but non-empty range" state the CLI must
  represent, expanding the surface for callers.

### Manual override per release

- Bad: re-introduces an out-of-band step. Defeats the goal of "the commit
  log is the input."
- Bad: humans get this wrong; that is exactly why the tool exists.
