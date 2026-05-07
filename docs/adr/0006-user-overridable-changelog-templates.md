# User-overridable changelog templates

- Status: Accepted
- Date: 2026-05-06

## Context and Problem Statement

Different teams want different changelog presentations: rST for Sphinx
projects, Markdown for GitHub releases, tabular for internal tooling,
HTML for status pages, and so on. The data behind a changelog (the
grouped commits, the version, the bump rules) is the same; only the
formatting differs.

If the tool hardcodes one format, every team that wants a different one
must either fork the tool or post-process its output. Both options
spread project-specific concerns into project-specific code.

## Decision Drivers

- Separate data from presentation — the data shape is a contract
  (ADR-0004), the formatting is a customer concern.
- Common cases must work out of the box; custom cases must work without
  forking.
- Custom templates must be discoverable via a stable, documented
  mechanism — not a hidden CLI flag combination.

## Considered Options

- Built-in default template + user-override via environment variable
  pointing at a template file.
- Built-in default + override via CLI flag only.
- Built-in template only; users post-process the JSON output.
- Plugin system (entry points or a Python module path).

## Decision Outcome

Chosen: **shipped default template plus user override via environment
variable** — and, where the subcommand exposes one, a CLI flag.

### Mechanism

Two override points exist, one per changelog mode:

| Mode             | Env var                              | CLI flag              | Default                                |
| ---------------- | ------------------------------------ | --------------------- | -------------------------------------- |
| `changelog`      | `PYGITVER_TEMPLATE_CHANGELOG`        | (none)                | `templates/changelog.tmpl`             |
| `changelogs`     | `PYGITVER_TEMPLATE_CHANGELOG_COMMON` | `-t/--template`       | `templates/changelog-common.tmpl`      |

Resolution order for the template:

1. CLI flag, if the subcommand has one.
2. The applicable environment variable.
3. The shipped default in the package.

The path is taken verbatim. In Docker contexts, users mount their template
into the container and pass a `/app/...` path.

### Templating engine

The shipped templates and the runtime use Jinja2. This is a *deliberately
internal* choice: a user supplying a custom template is supplying a Jinja2
template. The engine is not a contract in the same sense as the CLI is —
a future change to a different template engine would require migration of
custom templates and is therefore breaking, but the contract that this
ADR locks down is "the rendering engine is documented and the default
template ships with the package."

The template receives the same fields documented in ADR-0004:

- For `changelog`: `version`, `features`, `bugfixes`, `deprecations`,
  `docs`, `others`, `non_conventional_commit`.
- For `changelogs`: `version`, `services` — a mapping of service names
  to per-service changelog objects.

When the configured template path does not exist:

- For `changelog`: the rendered output contains an error string and the
  command exits 0 (current behavior; documented here for transparency,
  flagged in Consequences).
- For `changelogs`: a `ChangelogsMngrError` is raised, the message is
  printed, and the command exits 1.

### Consequences

- Good: any team can adopt the tool without forking.
- Good: data and presentation are cleanly separated; the JSON output
  (ADR-0004) is the engine-agnostic contract for callers who want to
  build their own renderer entirely.
- Good: defaults work for the common case (rST changelog), so most
  users never touch the override.
- Bad: the templating engine is leaked through user templates. A future
  engine change is a breaking change for everyone with a custom
  template. Mitigation: keep Jinja2 unless there is a strong reason to
  change.
- Bad: the two modes have inconsistent error handling on missing
  templates (silent error string vs. exit 1). Worth aligning; the
  alignment is a fix, not a contract change, because no caller can
  reasonably depend on the silent-error behavior.

## Pros and Cons of the Options

### Default + env var override (chosen)

- Good: env var is convenient in Docker and CI; stable across calls.
- Good: works for both Python and Docker users with the same syntax.
- Bad: env vars can be set unintentionally and persist across shells.

### Default + CLI flag only

- Good: explicit per-call.
- Bad: noisier in CI scripts that already have a stable template; users
  end up exporting an env var anyway.

### No customization (post-process JSON)

- Good: simplest possible tool.
- Bad: every consumer reinvents a tiny renderer.

### Plugin system

- Bad: heavyweight; requires a Python install for the plugin, defeats
  the Docker-friendly distribution model (ADR-0005).
- Bad: YAGNI — no consumer has asked for programmatic plugin behavior;
  data + template covers the cases that exist.
