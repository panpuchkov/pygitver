import subprocess

import pytest


class GitRepo:
    """A throwaway git repository the current directory is switched into."""

    def git(self, *args: str) -> str:
        return subprocess.run(
            [
                "git",
                "-c", "user.name=pygitver-tests",
                "-c", "user.email=pygitver-tests@example.com",
                "-c", "commit.gpgsign=false",
                "-c", "tag.gpgsign=false",
                "-c", "core.hooksPath=/dev/null",
                *args,
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def commit(self, message: str) -> str:
        self.git("commit", "--quiet", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def tag(self, name: str) -> None:
        self.git("tag", "-a", name, "-m", f"Release: {name}")

    def checkout(self, ref: str) -> None:
        self.git("checkout", "--quiet", ref)


@pytest.fixture
def git_repo(tmp_path, monkeypatch) -> GitRepo:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PYGITVER_VERSION_PREFIX", raising=False)
    repo = GitRepo()
    repo.git("init", "--quiet", "--initial-branch=main")
    return repo
