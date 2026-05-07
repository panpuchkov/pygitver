import json
import sys

import pytest

from pygitver.git import Git
from pygitver.pygitver import main


def test_get_version_uses_package_metadata(monkeypatch):
    from pygitver import _get_version

    monkeypatch.setattr("pygitver._pkg_version", lambda _: "9.9.9")
    assert _get_version() == "9.9.9"


def test_get_version_falls_back_when_package_not_installed(monkeypatch):
    from importlib.metadata import PackageNotFoundError

    from pygitver import _get_version

    def raising(_):
        raise PackageNotFoundError

    monkeypatch.setattr("pygitver._pkg_version", raising)
    assert _get_version() == "unknown"


def test_main_with_no_args_prints_help_and_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["pygitver"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code != 0
    captured = capsys.readouterr()
    assert "usage:" in (captured.out + captured.err).lower()


def test_main_rejects_multiple_actions(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["pygitver", "-cv", "-nv"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code != 0
    err = capsys.readouterr().err
    assert "only one" in err.lower()


def test_check_commit_message_valid_exits_zero(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["pygitver", "-ccm", "feat: new thing"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0


def test_check_commit_message_invalid_exits_nonzero_with_guidance(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["pygitver", "-ccm", "not conventional"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "Conventional Commits" in out


def test_cli_surfaces_git_command_failure(monkeypatch, capsys):
    # When _cmd's subprocess returns non-zero, the CLI exits with that
    # return code and prints the git output. Pin so any reshaping of
    # GitError preserves the user-facing behavior.
    class FakeResult:
        returncode = 128
        stdout = b"fatal: not a git repository\n"

    monkeypatch.setattr("pygitver.git.subprocess.run", lambda *a, **kw: FakeResult())
    monkeypatch.setattr(sys, "argv", ["pygitver", "-t"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 128
    out = capsys.readouterr().out
    assert "fatal: not a git repository" in out


def test_changelog_subcommand_does_not_leak_sentinel_to_git(monkeypatch, capsys):
    # On a tagless repo, version_current() returns the sentinel "v0.0.0".
    # The CLI must not pass that sentinel to `git log` as a real ref —
    # `git log v0.0.0...HEAD` fails because the tag doesn't exist.
    monkeypatch.setattr(Git, "tags", lambda **kwargs: [])

    captured = []

    def fake_cmd(*args: str) -> str:
        captured.append(list(args))
        if args[:3] == ("git", "log", "--pretty=format:%s"):
            return "fix: a fix\nfeat: a feature"
        return ""

    monkeypatch.setattr(Git, "_cmd", fake_cmd)
    monkeypatch.setattr(sys, "argv", ["pygitver", "changelog", "--format", "json"])

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0

    log_argv = next(c for c in captured if c[:3] == ["git", "log", "--pretty=format:%s"])
    assert not any(part.startswith("v0.0.0...") for part in log_argv), (
        f"sentinel leaked into git argv: {log_argv}"
    )

    out = capsys.readouterr().out
    payload = json.loads(out.strip())
    assert "a fix" in payload["changelog"]["bugfixes"]
    assert "a feature" in payload["changelog"]["features"]
