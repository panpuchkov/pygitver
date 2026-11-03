# The bump range holds only commits on HEAD's side of the current tag

- Status: Accepted
- Date: 2026-11-03

## Context and Problem Statement

ADR-0003 derives the bump from "a range of commits between two refs", and
ADR-0004 returns the current version unchanged "when the commit range is
empty". Neither says which commits form the range.

The range was `<current>...HEAD`, the symmetric difference. ADR-0002 takes
the current version from tags across all branches, so the current tag need
not be in HEAD's history. On a commit *behind* the current tag, the range
held the tag's own newer commits, and `--next-ver` bumped past a version the
commit doesn't contain. A CI job that tags whenever `--next-ver` differs
from `--curr-ver` then released an older commit under a higher version:
two builds of a monorepo service ran in parallel, and the slower one, on an
older commit, tagged `0.4.0` after `0.3.0` existed on a newer commit.

## Decision Drivers

- An older commit must never produce a version above the current one.
- New commits on HEAD must keep bumping exactly as ADR-0003 defines.
- ADR-0002's "tags across all branches" must keep working.

## Considered Options

- Range `<current>..HEAD`: commits reachable from HEAD but not from the
  current tag (this ADR).
- Keep `<current>...HEAD`, and restrict the current version to tags reachable
  from HEAD.
- Keep the range, and leave the check to each CI caller.

## Decision Outcome

Chosen: **`<current>..HEAD`**, for `--next-ver` and for `changelog`.

- On a commit behind the current tag, the range is empty, so `--next-ver`
  equals `--curr-ver` and a caller comparing the two creates no tag.
- On a branch whose history doesn't contain the current tag, only the
  branch's own commits drive the bump.
- A `changelog --start A --end B` lists the commits B has and A lacks.

### Consequences

- Good: an older commit can't be released above the current version.
- Good: ADR-0002 and ADR-0003 hold unchanged; only the range is defined.
- Bad: `changelog --start` with a ref that isn't an ancestor of `--end` no
  longer lists the start side's commits. That was never a meaningful
  changelog.

## Pros and Cons of the Options

### Range `<current>..HEAD`

- Good: one-character change; matches what "commits since the last release"
  means.
- Good: keeps the current version global, as ADR-0002 requires.

### Current version restricted to tags reachable from HEAD

- Bad: reverses ADR-0002: a release-branch tag would no longer be seen from
  a feature branch.
- Bad: an older commit with its own untagged commits would bump from an older
  tag and could produce a version that already exists elsewhere.

### Leave the check to each CI caller

- Bad: every caller repeats the same reachability check; any that forgets it
  releases older commits under higher versions.
