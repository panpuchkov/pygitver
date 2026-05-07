# Shell out to the git CLI via subprocess

- Status: Accepted
- Date: 2026-05-06

## Context and Problem Statement

The tool needs to read tags, list commits over a range, fetch from
remotes, and query the installed git version. There are two broad ways to
do this: link against a git library (libgit2 bindings, an in-language
git client) or shell out to the `git` binary that the user already has.

The choice has user-visible consequences: it changes runtime
dependencies, behavior under unusual repo configurations, and the
fidelity of error messages.

## Decision Drivers

- Behavior must match what the user sees in their own terminal.
- Runtime footprint must stay small — the tool is invoked from git hooks,
  where startup time and memory matter.
- Repository support must be as broad as `git` itself: shallow clones,
  worktrees, alternates, custom hooks, SSH/HTTPS auth — every config a
  user might have.
- Avoid adding a runtime dependency that has its own release cadence and
  CVE surface unless it earns its place.

## Considered Options

- Shell out to the `git` binary via `subprocess`.
- Use a Python git library (e.g., GitPython, dulwich, pygit2).
- Implement just the git operations we need from scratch (read tag refs,
  walk commit log).

## Decision Outcome

Chosen: **shell out to the system `git` binary via Python's
`subprocess`**.

### Constraints this places on consumers

- `git` must be on PATH at runtime. The Docker image bundles it; the pip
  channel relies on the user having it (universally true for anyone
  who could possibly want this tool).
- The tool runs git commands without a working-directory override, so it
  must be invoked from inside a git repository (or a path the user has
  `cd`'d into).
- All git operations use the user's existing git config: credentials,
  SSH keys, signing config, hooks. The tool does not bring its own
  authentication or override `core.*` settings.

### Implementation invariants (internal, but informative)

- Commands are invoked with a fixed argv list — never via `shell=True`.
- Stderr is merged into stdout for the wrapped runner; non-zero exit
  codes raise `GitError` carrying the exit code and the captured output.
- Output is decoded as UTF-8; locale-dependent git messages may produce
  garbled diagnostic text. Acceptable: the data we parse (tag names,
  commit subjects) is locale-independent; only error messages are
  affected.

### Consequences

- Good: behavior matches the user's own `git` invocations exactly. Bug
  reports translate one-to-one between "the tool says X" and "what does
  `git ...` say."
- Good: zero git-related runtime dependencies in the package. Only
  Jinja2 ships, and that is for templating, not git.
- Good: every git feature works automatically — partial clones, sparse
  checkouts, worktrees, custom remotes, GPG-signed tags, etc.
- Good: the user's git upgrade is the tool's git upgrade. No tracking
  CVEs in a bundled library.
- Bad: parsing git output is brittle to format changes across git
  versions. Mitigation: we use `--pretty=format:` with explicit format
  specifiers and `--sort=-v:refname`, both stable contracts in git for
  many years.
- Bad: subprocess startup cost is paid on every invocation. Negligible
  for the tool's usage patterns (one invocation per commit, one per
  release).
- Bad: command construction currently uses `command.split(" ")` rather
  than passing argv as a list. This is fragile if any future code path
  needs to pass a path with spaces. Mitigation: noted as a known
  constraint; converting to argv lists is a fix that does not change
  behavior for current callers.
- Bad: `subprocess` exit codes leak through to callers as the CLI's exit
  code, which is *intended* (see ADR-0004) but couples the tool's exit
  code surface to git's. A change in git's exit codes would propagate.

## Pros and Cons of the Options

### Subprocess to system git

- Good: matches user behavior exactly; zero deps.
- Bad: requires git on PATH; output parsing is text-based.

### Python git library (GitPython, dulwich, pygit2)

- Good: structured access to refs and objects; no parsing.
- Bad: extra runtime dependency for every install — including the
  Docker image, which currently relies on the system git binary it
  already needs anyway.
- Bad: behavior may diverge from the system git in edge cases (custom
  hooks, signed tags, alternates), especially in pure-Python clients.
- Bad: bigger CVE surface and an independent release cadence to track.

### Re-implement from scratch

- Bad: enormous scope — refs, packfiles, alternates, signature
  verification, transport. The "small subset we need" rule rarely
  survives contact with real-world repositories.
- Bad: zero benefit over either prior option; the tool gains no new
  capability and inherits all the maintenance burden.
