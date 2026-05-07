# Multi-app monorepo support via PYGITVER_VERSION_PREFIX

- Status: Accepted
- Date: 2026-05-06

## Context and Problem Statement

A repository may host more than one independently-released artifact —
several services in a monorepo, a library plus a sample application, a
client and a server, etc. Each artifact has its own version timeline.
A single global `vX.Y.Z` tag namespace conflates them: a `feat:` in
`service_a` would otherwise bump the version that `service_b`'s
deployment also reads.

We need a way for one repository to carry multiple, independent
version streams without inventing a configuration file format and
without breaking single-version repositories that work fine today.

## Decision Drivers

- Single-version repositories must continue to work with no
  configuration whatsoever.
- Multi-version setups must not require a project-local config file
  the tool has to read and validate.
- The tool must remain stateless — a CI job that runs once must not
  depend on persistent state between runs.
- The mechanism must compose with the existing CLI; no new commands.

## Considered Options

- A version-prefix env var that filters tags and is preserved through
  the bump (this ADR).
- A configuration file in the repo (e.g., `pygitver.toml`) listing
  artifacts and their tag prefixes.
- A CLI flag on each invocation.
- A separate sub-tool or alternate entry point for monorepos.

## Decision Outcome

Chosen: **`PYGITVER_VERSION_PREFIX` environment variable**.

### Behavior

- When `PYGITVER_VERSION_PREFIX` is unset or empty, the tool considers
  all tags that match the version regex defined in ADR-0002.
- When `PYGITVER_VERSION_PREFIX` is set:
  - `--curr-ver` returns the most recent tag whose name starts with
    the configured prefix and matches the version regex; if no such
    tag exists, the sentinel `v0.0.0` is returned (same fallback as
    the unprefixed case).
  - `--next-ver` strips the prefix, applies the bump rules, and
    re-prepends the prefix to produce the new version string.
  - `changelog` ranges default to the most recent prefix-matching tag
    as the start, when no `--start` is given.
- The prefix may contain lowercase letters, hyphens, and underscores
  (`[a-z_-]`), per the version regex's prefix class. It must end
  before any digit — for example `app_a_` is valid; `v2_` is not
  because the prefix would be split mid-word by the digit.

### Usage example

```
$ git tag -l
app_a_1.2.3
app_b_2.5.2

$ PYGITVER_VERSION_PREFIX=app_a_ pygitver --curr-ver
app_a_1.2.3

$ PYGITVER_VERSION_PREFIX=app_a_ pygitver --next-ver
app_a_1.3.0           # given a feat in the range

$ PYGITVER_VERSION_PREFIX=app_b_ pygitver --next-ver
app_b_2.5.3           # given a fix in the range
```

In CI, each artifact's pipeline exports its own prefix before invoking
the tool; the tool itself does not need to know how many artifacts
exist or which is which.

### Consequences

- Good: zero configuration for single-version repos — the common case.
- Good: monorepo support is one env var, settable per CI job, with no
  state leaking between artifacts.
- Good: the tool stays stateless; no config file to parse or validate.
- Good: prefix passes through cleanly to `--next-ver`, producing
  correctly-prefixed output that can be fed straight into `git tag`.
- Bad: nothing prevents two artifacts from sharing a prefix; this is
  a process problem the tool cannot detect from history alone.
- Bad: the changelog command's range computation only considers the
  tag namespace it sees through the prefix filter, but a `feat:` in
  the commit log is not itself scoped to an artifact. A monorepo
  using this feature still relies on the team's discipline (e.g.,
  scope in commits, or path-filtered CI) to keep changelogs honest.
  The tool documents this rather than trying to enforce it.
- Bad: the prefix is structural to the tag (must satisfy the version
  regex); arbitrary separators are not allowed.

## Pros and Cons of the Options

### Env var prefix (chosen)

- Good: stateless, composable, no new files.
- Good: works the same in pip and Docker channels.
- Bad: callers must remember to set it; an unset prefix in a
  monorepo silently behaves like the global namespace.

### Repo-local config file

- Good: a single source of truth for which artifacts exist.
- Good: enables cross-artifact validation (e.g., reject duplicate
  prefixes).
- Bad: introduces a parser, a schema, a format-versioning story, and
  a validation surface for every release.
- Bad: violates "stateless tool"; the tool now depends on a file in
  the working directory.

### Per-call CLI flag

- Good: explicit at the call site.
- Bad: every CI step that invokes the tool — and there can be many —
  must pass the flag, where an env var is set once.
- Bad: easier to forget on one of the calls, leading to silent
  cross-artifact bumps.

### Separate sub-tool for monorepos

- Bad: doubles the surface to maintain.
- Bad: re-implements 90% of the existing CLI for the 10% that differs.
