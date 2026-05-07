# Dual distribution: pip package and Docker image

- Status: Accepted
- Date: 2026-05-06

## Context and Problem Statement

The tool's audience splits cleanly into two camps:

1. **Python projects** that already have a Python interpreter and a
   virtualenv discipline. They want a `pip install` and a binary on PATH.
2. **Non-Python projects** — Go, Node, Rust, monorepos with mixed stacks,
   plus CI runners that prefer ephemeral containers. They do not want to
   bring up a Python toolchain just to lint a commit message or compute a
   version.

Forcing camp 2 to install Python is a deal-breaker: the commit-msg git
hook would need a Python install on every developer machine and on every
CI runner, which is exactly the friction the tool is meant to remove.

## Decision Drivers

- Reach: support both Python and non-Python repositories.
- Reproducibility: the same tool version must produce the same output
  whether invoked via pip or Docker.
- Hook ergonomics: the commit-msg hook must work without assuming a
  Python install on the developer's machine.
- Maintenance cost: one source of truth for behavior — the CLI — must be
  exercised the same way in both channels.

## Considered Options

- Ship both a pip package and a Docker image, with the same CLI contract.
- Pip-only.
- Docker-only.
- A statically-linked native binary.

## Decision Outcome

Chosen: **ship both a pip package and a Docker image**, with the CLI
contract from ADR-0004 as the shared surface.

### Pip channel

- Package: `pygitver` on PyPI.
- Entry point: `pygitver = "pygitver.pygitver:main"`.
- Install: `pip install pygitver`. Requires Python and a system `git`
  binary on PATH (see ADR-0007).

### Docker channel

- Image: `panpuchkov/pygitver` on Docker Hub.
- Base: `python:3.12-alpine` (build and runtime).
- Entrypoint: the `pygitver` binary; arguments pass through.
- Bundled: a system `git` (apk-installed) and `openssh` (for tag fetches
  over SSH-based remotes).
- Tags: `latest` for the most recent release; immutable per-version tags
  for reproducible CI pinning.
- Architectures: `amd64` and `arm64`.

### Git hook deliberately runs Docker

The shipped commit-msg hook (`src/pygitver/scripts/git/hooks/commit-msg`)
invokes the Docker image, not the pip CLI:

```
docker run --rm -v $(pwd):/app -w /app panpuchkov/pygitver \
  --check-commit-message "$(cat $1)"
```

This is intentional. The hook must run on developer machines that do not
have Python installed. Requiring `docker` is a smaller imposition than
requiring `python + pygitver` for non-Python repositories, which are the
ones that most need commit-message linting in the first place.

### Consequences

- Good: every project class can adopt the tool with at most one
  dependency they probably already have.
- Good: CI configurations can pin a docker tag for fully reproducible
  builds; the pip channel similarly supports `pygitver==X.Y.Z`.
- Good: behavior parity is enforced by both channels exposing the same
  CLI; tests run against the CLI surface, so divergence shows up in CI.
- Bad: every release must publish two artifacts. CI must build, tag, and
  push to both PyPI and Docker Hub. Operationally heavier than a single
  channel.
- Bad: the docker hook hardcodes `panpuchkov/pygitver` (no version pin).
  This means hooks track `latest` and inherit any future breaking
  changes. Mitigation candidate (out of scope for this ADR): the
  installer could substitute the current pinned tag at install time.
- Bad: docker pull on every commit adds latency on the first commit per
  shell session and after image pruning. Acceptable in practice because
  the image is cached.
- Bad: `arm64` images and `amd64` images must both be released, doubling
  build matrix size. Already addressed; documented here for completeness.

## Pros and Cons of the Options

### Pip + Docker

- Good: covers both audiences.
- Good: hook is portable to non-Python repos.
- Bad: two release artifacts.

### Pip-only

- Good: simpler release pipeline.
- Bad: forces non-Python repositories to install Python just for a git
  hook. This was the original blocker.

### Docker-only

- Good: simpler than dual-channel.
- Good: hermetic — fewer "works on my machine" reports.
- Bad: forces Python repositories that already have a virtualenv to
  install Docker for a tool that is, technically, just Python.
- Bad: docker invocation overhead is felt more in shell pipelines than in
  CI; pip users would notice.

### Native statically-linked binary

- Good: zero runtime deps, fastest startup.
- Bad: requires re-implementing the tool in a language with native-binary
  toolchains. Out of scope for this decision; it is an implementation
  question, not a distribution one.
