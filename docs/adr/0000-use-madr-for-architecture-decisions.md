# Use MADR for architecture decisions

- Status: Accepted
- Date: 2026-05-06
- Deciders: pygitver maintainers

## Context and Problem Statement

pygitver has accumulated several load-bearing decisions (commit format, version
source, bump rules, distribution channels, CLI shape) that are encoded only in
code and commit history. New contributors must reverse-engineer the rationale,
and there is no shared place to record future decisions or supersessions.

We need a lightweight, durable way to capture the *why* behind significant
choices so that future maintainers — and any future re-implementation of the
tool — can preserve, revisit, or revise them deliberately rather than
accidentally.

## Decision Drivers

- Decisions must outlive the people who made them.
- Format must be readable in a plain text editor and diff well in git.
- Overhead per ADR must be low enough that contributors actually write them.
- The format should make tradeoffs (what was rejected, and why) explicit.

## Considered Options

- MADR (Markdown Any Decision Record), v4.x.
- Nygard's classic ADR template (Context / Decision / Status / Consequences).
- A custom minimal template.
- No formal template; rely on commit messages and code comments.

## Decision Outcome

Chosen: **MADR**.

ADRs live in `docs/adr/` as `NNNN-kebab-title.md`, where `NNNN` is a
zero-padded sequence number assigned at creation time and never reused.

Each ADR includes: Status, Date, Context and Problem Statement, Decision
Drivers, Considered Options, Decision Outcome (with Consequences), and Pros
and Cons of the Options.

Status lifecycle: `Proposed` → `Accepted` → (`Deprecated` | `Superseded by
ADR-NNNN`). An accepted ADR is immutable in substance; corrections fix typos
and broken links only. Reversing a decision means writing a new ADR that
supersedes the old one and updating the old one's status.

### Consequences

- Good: rationale is searchable, diff-able, and reviewable in pull requests.
- Good: the "Considered Options" section forces contributors to articulate
  what they rejected and why — useful both at the time and in retrospect.
- Good: language-agnostic; the decisions survive any re-implementation.
- Bad: minor process overhead — a non-trivial change now requires an ADR.
- Bad: ADRs can drift from code if not enforced. Mitigation: review treats
  ADR omission as a review comment for any change touching items listed in
  this directory.

## Pros and Cons of the Options

### MADR

- Good: explicit "Considered Options" and per-option pros/cons.
- Good: de-facto standard with public template and tooling support.
- Good: structured enough for consistency, short enough to write quickly.
- Bad: slightly more sections than Nygard, marginal extra effort.

### Nygard classic

- Good: minimal — Context, Decision, Status, Consequences only.
- Bad: rejected alternatives have no dedicated home, so they tend to be
  omitted, which is the most useful information in retrospect.

### Custom minimal template

- Bad: drift from a known standard means contributors and tooling cannot
  rely on shape, and we would re-invent fields over time.

### No template

- Bad: status quo. The information vanishes into commit messages and PR
  descriptions and is not searchable as a coherent set of decisions.
