# The CLI is the public contract

- Status: Accepted
- Date: 2026-05-06

## Context and Problem Statement

pygitver is consumed almost entirely from automation: shell scripts, CI
pipelines, and git hooks. None of those import the Python module — they
exec a binary or a docker container, read stdout, and branch on the exit
code.

That means the CLI surface — flags, subcommands, exit codes, stdout
shape, and JSON schema — *is* the API. Internal Python class and function
names are implementation details. Any change visible from the shell is a
change to the public contract and must be treated with the same care as
breaking an API.

## Decision Drivers

- Downstream consumers depend on the shape of stdout, not on Python
  internals.
- A stable contract means CI scripts written today still work next year.
- Both the pip CLI and the Docker image must expose the *same* contract
  (see ADR-0005).
- Programmatic consumers want JSON; humans want plain text. Both must be
  available.

## Considered Options

- Treat the CLI as a public contract; document its surface and version it
  alongside SemVer rules.
- Treat the Python API as the contract and let the CLI evolve freely.
- Treat *both* as contracts.

## Decision Outcome

Chosen: **the CLI is the public contract; the Python API is internal.**

### CLI surface (frozen unless changed by a new ADR)

Commands and flags currently in scope:

- `-v`, `--version` — prints `pygitver <version>` and exits 0.
- `-cv`, `--curr-ver` — prints the current version on a single line, exit 0.
  When no matching tag exists, prints the sentinel `v0.0.0`.
- `-nv`, `--next-ver` — prints the next bumped version on a single line,
  exit 0. When no prior version tag exists, the bump is computed against
  the full commit history and the result starts at `v0.0.1` (per
  ADR-0003). When the commit range is empty and a real tag exists, the
  current version is returned unchanged.
- `-t`, `--tags` — prints all git tags, one per line, sorted descending.
- `-ccm`, `--check-commit-message <msg>` — exits 0 if `<msg>` is a valid
  Conventional Commit (per ADR-0001), else prints an error and exits 1.
- `changelog [-s START] [-e END] [-f text|json]` — prints the changelog
  for the range (`START`..`END`). Defaults: `START` = current version
  tag, `END` = `HEAD`, `f` = `text`. **Asymmetry with `--next-ver`:** if
  no version tag exists, `START` defaults to the sentinel `v0.0.0`,
  which is not a real ref. Git's exit code for the failed `git log`
  invocation is propagated as the CLI's exit code, so `changelog` on a
  tagless repo fails where `--next-ver` succeeds. Documented as a known
  asymmetry; consumers that want to render a changelog on a fresh repo
  must pass an explicit `--start` (e.g., the first commit hash).
- `changelogs -d <DIR> [-clsv VERSION] [-f text|json] [-t TEMPLATE]` —
  aggregates per-service JSON changelogs from `DIR` into a combined
  document (see ADR-0006).

Exit code conventions:

- `0` — success, including queries that legitimately return the
  sentinel (e.g., `--curr-ver` on a tagless repo).
- `1` — invalid input (bad commit message, unknown `--format` value,
  missing template for `changelogs`).
- The exact `git` exit code passed through, when an underlying git
  invocation fails (transported via `GitError` in implementation; what
  callers see is the same numeric code git would have given them). This
  applies, for example, to `changelog` on a tagless repo (see the
  asymmetry note above).

Stdout/stderr split:

- Today, both successful output and error diagnostics print to
  **stdout**. The contract this ADR locks down is the success-case
  output and exit-code semantics — not the channel the diagnostics use.
  Routing diagnostics to stderr in the future is a fix, not a contract
  break.

Format flag:

- `text` is intended for humans; the exact wording may evolve.
- `json` is the machine contract; the schema is part of this ADR and
  changes to it require a major bump.

### JSON schema for `changelog --format json`

```json
{
  "version": "<string, e.g. v0.2.6 or app_a_1.3.0>",
  "bump_rules": {
    "major": <bool>,
    "minor": <bool>,
    "patch": <bool>
  },
  "changelog": {
    "features":                ["<string>", ...],
    "bugfixes":                ["<string>", ...],
    "deprecations":            ["<string>", ...],
    "others":                  ["<string>", ...],
    "docs":                    ["<string>", ...],
    "non_conventional_commit": ["<string>", ...]
  }
}
```

Field guarantees: every key in `changelog` is always present; values are
always arrays (possibly empty); strings are commit subjects with the
Conventional Commits prefix stripped.

### JSON schema for `changelogs --format json`

```json
{
  "version": "<aggregated version string>",
  "services": {
    "<service-name>": { /* per-service changelog object as above */ }
  }
}
```

### Consequences

- Good: callers can rely on a documented surface; CI scripts are stable.
- Good: the schema doubles as input documentation for downstream tools
  that consume the JSON.
- Good: the contract is the same across pip and Docker (ADR-0005).
- Bad: the Python module structure is *not* a contract. Importing
  `pygitver.git.Git` from another Python package is unsupported; it may
  be renamed, refactored, or moved without an ADR. Internal users must
  shell out like everyone else.
- Bad: today error messages and diagnostics print to stdout rather
  than stderr (e.g., `print("ERROR: ...")` followed by `exit(1)`). This
  ADR explicitly does not lock that in. A future change to route
  diagnostics to stderr is a fix, not a contract break.
- Bad: `changelog` on a tagless repo fails (git exit code propagated)
  while `--next-ver` succeeds. This asymmetry is documented but not
  cleaned up here; either subcommand could be aligned with the other
  in a future ADR.
- Bad: argparse's `-h`/`--help` text is generated from the parser and is
  not stable across Python versions; help output is documentation only,
  not contract.

## Pros and Cons of the Options

### CLI as the contract

- Good: matches how the tool is actually consumed.
- Good: keeps the Python implementation free to refactor.
- Bad: requires discipline — CLI changes must go through ADR review.

### Python API as the contract

- Bad: virtually no consumers import the module.
- Bad: locks the implementation to public class names and method
  signatures, making any refactor a breaking change for users who do
  not exist.

### Both APIs as contracts

- Bad: doubles the surface to maintain for no demonstrated demand.
- Bad: violates YAGNI; can be revisited if a real Python consumer
  emerges and asks for a stable Python API.
