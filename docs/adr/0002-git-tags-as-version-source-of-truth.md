# Git tags are the source of truth for versions

- Status: Accepted
- Date: 2026-05-06

## Context and Problem Statement

Some projects record the current version in a file (`VERSION`, a constant
in source, `package.json`, etc.). Doing so creates a "release commit" whose
sole purpose is to bump that file, and creates the possibility for the file
and the actual published artifact to disagree.

We need a single, authoritative location for the version of a release, that
is reachable both at release time and from any past commit, and that does
not require a write-back commit after publication.

## Decision Drivers

- One source of truth — code and tag must never disagree.
- No "release commit" round-trip required after publishing.
- History queryable: at any commit, the tool must answer "what is the most
  recent released version reachable from here?"
- No build-time codegen for embedding versions.

## Considered Options

- Annotated git tags as the single source of truth.
- A version file in the working tree (e.g., `VERSION`).
- A version constant in source (e.g., `__version__` in a Python module).
- A combination: file plus a tag, kept in sync by tooling.

## Decision Outcome

Chosen: **annotated or lightweight git tags as the source of truth**.

The "current version" is defined as the most recent tag, in `git tag -l
--sort=-v:refname` order, that:

1. Starts with the active prefix (empty by default; see ADR-0008).
2. Matches the regex `^[a-z\-_]*\d+\.\d+\.\d+(?:-[a-zA-Z\d.]+)?$` —
   i.e., an optional lowercase prefix of `[a-z_-]`, three numeric
   components, and an optional pre-release suffix.

If no tag matches, the current version is reported as `v0.0.0` (a sentinel),
and this fact is what allows the bump command (see ADR-0003) to detect the
"no prior version" case and refuse rather than emit a value.

Tags are searched across all branches, not only the current branch — so
that a tag created on a release branch is still discoverable from a
feature branch.

The tool itself never creates, moves, or deletes tags. Tag creation is the
release operator's responsibility (typically `git tag` followed by `git
push --tags`, or a CI job).

### Consequences

- Good: one source of truth — `git tag` is the only place a version exists.
- Good: no release commit needed post-publish; the tag *is* the release
  marker.
- Good: every commit can answer "what version preceded me?" by walking
  reachable tags.
- Good: works on any host — the contract is git, not GitHub or GitLab.
- Bad: the tool requires a real git repository on disk with tags reachable.
  In a shallow CI clone, the version may be wrong if tags were not fetched.
  Mitigation: `tags(update_from_remote=True)` exposes a `git fetch
  --all --tags` step that callers can run before querying.
- Bad: any user with push rights can create or delete tags. Versioning
  integrity therefore depends on repository access controls.
- Bad: pre-release ordering follows `git`'s `-v:refname` rules, which are
  alphanumeric and not strictly SemVer 2.0.0 pre-release ordering. For
  example, `1.0.0-rc.10` sorts after `1.0.0-rc.2` correctly under
  `version sort`, but exotic pre-release strings can surprise. Acceptable
  for the cases the tool is used in today.

## Pros and Cons of the Options

### Git tags as source of truth

- Good: native to git; no extra infrastructure.
- Good: tags survive forks and clones.
- Bad: requires shipping or fetching tags into CI.

### Version file in the working tree

- Bad: bumping the version requires a commit, which then needs a tag,
  which is a two-step dance and a frequent source of "tagged commit ≠
  file content" bugs.
- Bad: rebases and merges can corrupt the file; humans miss conflicts.

### Version constant in source

- Bad: same problems as a version file, plus build-time embedding
  (we would need codegen or import-time file reads).
- Bad: tying the *tool's own* version to a tag (which we do via
  `Git.__version__`) is fine for *this* tool's identity; tying *every
  consumer's* version to a constant in their source is the antipattern
  this ADR rejects for consumers.

### File plus tag

- Bad: two sources of truth and a synchronization rule. Worst-of-both.
