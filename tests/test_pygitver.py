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


def run_cli(monkeypatch, capsys, *args):
    monkeypatch.setattr(sys, "argv", ["pygitver", *args])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    return capsys.readouterr().out.strip()


def test_next_ver_on_a_commit_behind_the_current_tag_is_the_current_version(git_repo, monkeypatch, capsys):
    git_repo.commit("feat: a")
    git_repo.tag("v0.1.0")
    older = git_repo.commit("fix: b")
    git_repo.commit("feat: c")
    git_repo.tag("v0.2.0")
    git_repo.checkout(older)

    assert run_cli(monkeypatch, capsys, "--curr-ver") == "v0.2.0"
    assert run_cli(monkeypatch, capsys, "--next-ver") == "v0.2.0"


def test_next_ver_with_a_prefix_on_a_commit_behind_the_current_tag_is_the_current_version(
    git_repo, monkeypatch, capsys
):
    git_repo.commit("feat: a")
    git_repo.tag("app_a_0.1.0")
    older = git_repo.commit("fix: b")
    git_repo.commit("feat: c")
    git_repo.tag("app_a_0.2.0")
    git_repo.tag("app_b_1.0.0")
    git_repo.checkout(older)
    monkeypatch.setenv("PYGITVER_VERSION_PREFIX", "app_a_")

    assert run_cli(monkeypatch, capsys, "--curr-ver") == "app_a_0.2.0"
    assert run_cli(monkeypatch, capsys, "--next-ver") == "app_a_0.2.0"


def test_next_ver_bumps_by_commits_on_top_of_the_current_tag(git_repo, monkeypatch, capsys):
    git_repo.commit("feat: a")
    git_repo.tag("v0.2.0")
    git_repo.commit("fix: x")

    assert run_cli(monkeypatch, capsys, "--next-ver") == "v0.2.1"


def test_next_ver_on_a_branch_bumps_only_by_its_own_commits(git_repo, monkeypatch, capsys):
    # The current tag sits on another branch (ADR-0002): its commits must not bump this one.
    base = git_repo.commit("feat: a")
    git_repo.tag("v0.1.0")
    git_repo.git("checkout", "--quiet", "-b", "release")
    git_repo.commit("feat: r")
    git_repo.tag("v0.2.0")
    git_repo.git("checkout", "--quiet", "-b", "feature", base)
    git_repo.commit("fix: f")

    assert run_cli(monkeypatch, capsys, "--curr-ver") == "v0.2.0"
    assert run_cli(monkeypatch, capsys, "--next-ver") == "v0.2.1"


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
    captured = capsys.readouterr()
    assert "Conventional Commits" in captured.err
    assert "Conventional Commits" not in captured.out


def test_cli_surfaces_git_command_failure(monkeypatch, capsys):
    # When _cmd's subprocess returns non-zero, the CLI exits with that
    # return code and prints the git output to stderr.
    class FakeResult:
        returncode = 128
        stdout = b"fatal: not a git repository\n"

    monkeypatch.setattr("pygitver.git.subprocess.run", lambda *a, **kw: FakeResult())
    monkeypatch.setattr(sys, "argv", ["pygitver", "-t"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 128
    captured = capsys.readouterr()
    assert "fatal: not a git repository" in captured.err
    assert "fatal: not a git repository" not in captured.out


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
