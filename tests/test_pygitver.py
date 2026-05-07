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


def test_changelog_subcommand_does_not_leak_sentinel_to_git(monkeypatch, capsys):
    # On a tagless repo, version_current() returns the sentinel "v0.0.0".
    # The CLI must not pass that sentinel to `git log` as a real ref —
    # `git log v0.0.0...HEAD` fails because the tag doesn't exist.
    monkeypatch.setattr(Git, "tags", lambda **kwargs: [])

    captured = []

    def fake_cmd(command: str) -> str:
        captured.append(command)
        if "git log --pretty=format:%s" in command:
            return "fix: a fix\nfeat: a feature"
        return ""

    monkeypatch.setattr(Git, "_cmd", fake_cmd)
    monkeypatch.setattr(sys, "argv", ["pygitver", "changelog", "--format", "json"])

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0

    log_cmd = next(c for c in captured if "git log --pretty=format:%s" in c)
    assert "v0.0.0..." not in log_cmd, f"sentinel leaked into git command: {log_cmd}"

    out = capsys.readouterr().out
    payload = json.loads(out.strip())
    assert "a fix" in payload["changelog"]["bugfixes"]
    assert "a feature" in payload["changelog"]["features"]
