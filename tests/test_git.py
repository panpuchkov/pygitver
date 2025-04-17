import os
from pygitver.git import Git
from unittest import mock

GIT_LOG_OUTPUT_MOCK = "fix: test fix 1\n" \
                      "feat(api)!: new api\n" \
                      "fix(api)!: test fix 2\n" \
                      "docs: update doc\n" \
                      "deprecated: deprecated api\n" \
                      "some non-conventional commit\n" \
                      "refactor: code refactoring"


def test_version(monkeypatch):
    monkeypatch.setattr(Git, "_cmd", value=lambda *args, **kwargs: "git version 2.40.0")
    assert Git.git_version() >= "2.22.0"


def test_tags():
    # Note: git repo should have a tag with version v0.0.1. This check is not mocked.
    assert "v0.0.1" in Git.tags()


def test_version_current(monkeypatch):
    monkeypatch.setattr(Git, "tags", lambda: [])
    assert "0.0.0" == Git.version_current()

    monkeypatch.setattr(Git, "tags", lambda: ["0.0.2", "0.0.1"])
    assert "0.0.2" == Git.version_current()

    monkeypatch.setattr(Git, "tags", lambda: ["1.0.error"])
    assert "0.0.0" == Git.version_current()

    monkeypatch.setattr(Git, "tags", lambda: ["1.0.error", "0.1.2"])
    assert "0.1.2" == Git.version_current()

    monkeypatch.setattr(Git, "tags", lambda: ["R23.03-rc.1", "0.0.1", "0.0.0"])
    assert "0.0.1" == Git.version_current()

    monkeypatch.setattr(Git, "tags", lambda: ["R23.08.10-rc.1", "0.0.1", "0.0.0"])
    assert "0.0.1" == Git.version_current()

    monkeypatch.setattr(Git, "tags", lambda: ["v23.08.10-rc.1", "0.0.1", "0.0.0"])
    assert "v23.08.10-rc.1" == Git.version_current()

    monkeypatch.setattr(Git, "tags", lambda: ["service23.08.10-rc.1", "0.0.1", "0.0.0"])
    assert "service23.08.10-rc.1" == Git.version_current()

    monkeypatch.setattr(Git, "tags", lambda: ["service_a_0.1.1", "service_b_0.1.2", "service_c_2.1.0", "3.2.1", "0.0.0"])
    assert "service_a_0.1.1" == Git.version_current("service_a_")

    monkeypatch.setattr(Git, "tags", lambda: ["service_a_0.1.1", "service_b_0.1.2", "service_c_2.1.0", "3.2.1", "0.0.0"])
    assert "service_b_0.1.2" == Git.version_current("service_b_")


@mock.patch.dict(os.environ, {"PYGITVER_VERSION_PREFIX": "service_b_"}, clear=True)
def test_version_current_with_defined_prefix_b(monkeypatch):
    monkeypatch.setattr(Git, "tags", lambda: ["service_a_0.1.1", "service_b_0.1.2", "service_c_2.1.0", "3.2.1", "0.0.0"])
    assert "service_b_0.1.2" == Git.version_current()


@mock.patch.dict(os.environ, {"PYGITVER_VERSION_PREFIX": "service_a_"}, clear=True)
def test_version_current_with_defined_prefix_a(monkeypatch):
    monkeypatch.setattr(Git, "tags", lambda: ["service_a_0.1.1", "service_b_0.1.2", "service_c_2.1.0", "3.2.1", "0.0.0"])
    assert "service_a_0.1.1" == Git.version_current()


def test_changelog_group(monkeypatch):
    monkeypatch.setattr(Git, "changelog", value=lambda *args, **kwargs: GIT_LOG_OUTPUT_MOCK)
    monkeypatch.setattr(Git, "version_current", value=lambda: "1.2.3")

    # Test normalized commits
    res = Git.changelog_group(unique=True)
    expected_normalized = {
        'version': '2.0.0',
        'bump_rules': {
            'major': True,
            'minor': True,
            'patch': True
        },
        'changelog': {
            'features': [
                'new api'
            ],
            'bugfixes': [
                'test fix 1',
                'test fix 2'
            ],
            'deprecations': [
                'deprecated api'
            ],
            'others': [
                'code refactoring'
            ],
            'docs': [
                'update doc'
            ],
            'non_conventional_commit': [
                'some non-conventional commit'
            ]
        }
    }
    assert res == expected_normalized

    # Test duplicates
    monkeypatch.setattr(Git,
                        "changelog",
                        value=lambda *args, **kwargs: f"{GIT_LOG_OUTPUT_MOCK}\n{GIT_LOG_OUTPUT_MOCK}")
    monkeypatch.setattr(Git, "version_current", value=lambda: "1.2.0")
    res = Git.changelog_group(commit_wo_prefix=True, unique=True)
    assert res == expected_normalized

    monkeypatch.setattr(Git,
                        "changelog",
                        value=lambda *args, **kwargs: f"feat(api)!: new api\n{GIT_LOG_OUTPUT_MOCK}")
    monkeypatch.setattr(Git, "version_current", value=lambda: "1.2.0")
    res = Git.changelog_group(commit_wo_prefix=True, unique=True)
    assert res == expected_normalized

    # Test non-normalized commits
    monkeypatch.setattr(Git, "changelog", value=lambda *args, **kwargs: GIT_LOG_OUTPUT_MOCK)
    res = Git.changelog_group(commit_wo_prefix=False)
    assert res == {
        'version': '2.0.0',
        'bump_rules': {
            'major': True,
            'minor': True,
            'patch': True
        },
        'changelog': {
            'features': [
                'feat(api)!: new api'
            ],
            'bugfixes': [
                'fix: test fix 1',
                'fix(api)!: test fix 2'
            ],
            'deprecations': [
                'deprecated: deprecated api'
            ],
            'others': [
                'refactor: code refactoring'
            ],
            'docs': [
                'docs: update doc'
            ],
            'non_conventional_commit': [
                'some non-conventional commit'
            ]
        }
    }

    monkeypatch.setattr(Git, "changelog", value=lambda *args, **kwargs: GIT_LOG_OUTPUT_MOCK)
    monkeypatch.setattr(Git, "version_current", value=lambda: "1.2.0")
    res = Git.changelog_group(commit_wo_prefix=False,
                              end="1.0.0"
                              )
    assert res["version"] == '1.0.0'


def test_changelog_generate(monkeypatch):
    monkeypatch.setattr(Git, "changelog", value=lambda *args, **kwargs: GIT_LOG_OUTPUT_MOCK)
    monkeypatch.setattr(Git, "git_version", value=lambda *args, **kwargs: "git version v1.0.0")
    changelog = Git.changelog_generate(changelog_group=Git.changelog_group(),
                                       template_name="src/pygitver/templates/changelog.tmpl")
    assert changelog == "##########\nChange Log\n##########\n\nVersion v1.0.0\n=============\n\n\n\n\n\n" \
                        "Features\n--------\n\n\n* New api\n\n\n\n\n\n" \
                        "Bug Fixes\n---------\n\n\n* Test fix 1\n\n* Test fix 2\n\n\n\n\n\n" \
                        "Deprecations\n------------\n\n\n* Deprecated api\n\n\n\n\n" \
                        "Improved Documentation\n----------------------\n\n\n* Update doc\n\n\n\n\n" \
                        "Trivial/Internal Changes\n------------------------\n\n\n* Code refactoring\n\n"
    changelog = Git.changelog_generate(changelog_group=Git.changelog_group(),
                                       template_name="src/templates/no-template.tmpl")
    assert changelog.startswith("ERROR: Template ") is True


def test_bump_version_auto(monkeypatch):
    bump_rules = {"major": True, "minor": False, "patch": False}
    ver = Git.bump_version("", bump_rules)
    assert "1.0.0" == ver

    bump_rules = {"major": True, "minor": False, "patch": False}
    ver = Git.bump_version("1.2.0", bump_rules)
    assert "2.0.0" == ver


def test_bump_current_version_auto(monkeypatch):
    monkeypatch.setattr(Git, "version_current", value=lambda: "")

    bump_rules = {"major": True, "minor": False, "patch": False}
    ver = Git.bump_current_version(bump_rules)
    assert "1.0.0" == ver

    monkeypatch.setattr(Git, "version_current", value=lambda: "1.2.0")

    bump_rules = {"major": True, "minor": False, "patch": False}
    ver = Git.bump_current_version(bump_rules)
    assert "2.0.0" == ver

    bump_rules = {"major": True, "minor": True, "patch": False}
    ver = Git.bump_current_version(bump_rules)
    assert "2.0.0" == ver

    bump_rules = {"major": True, "minor": True, "patch": True}
    ver = Git.bump_current_version(bump_rules)
    assert "2.0.0" == ver

    ver = Git.bump_current_version({"major": False, "minor": True, "patch": False})
    assert "1.3.0" == ver

    ver = Git.bump_current_version({"major": False, "minor": True, "patch": True})
    assert "1.3.0" == ver

    ver = Git.bump_current_version({"major": False, "minor": False, "patch": True})
    assert "1.2.1" == ver


def test_version_prefix(monkeypatch):
    assert "" == Git._version_prefix("1.2.3")
    assert "v" == Git._version_prefix("v1.2.3")
    assert "v-" == Git._version_prefix("v-1.2.3")
    assert "v-v" == Git._version_prefix("v-v1.2.3")
    assert "v " == Git._version_prefix("v 1.2.3")


def test_version_validate():
    assert Git.version_validate("0.1.3") is True
    assert Git.version_validate("v0.1.3") is True
    assert Git.version_validate("0.1.3-rc1") is True
    assert Git.version_validate("v0.1.3-rc1") is True
    assert Git.version_validate("10.21.33") is True
    assert Git.version_validate("v10.21.33") is True
    assert Git.version_validate("10.21.33-rc1") is True
    assert Git.version_validate("v10.21.33-rc1") is True
    assert Git.version_validate("10.21.33") is True
    assert Git.version_validate("v10.21.33") is True
    assert Git.version_validate("10.21.33-rc1") is True
    assert Git.version_validate("v10.21.33-rc1.2-") is False


def test_check_commit_message():
    assert Git.check_commit_message("fix: test commit msg") is True
    assert Git.check_commit_message("fix(api): test commit msg") is True
    assert Git.check_commit_message("fix!: test commit msg") is True
    assert Git.check_commit_message("fix(api)!: test commit msg") is True
    assert Git.check_commit_message("feat: test commit msg") is True
    assert Git.check_commit_message("feat(api): test commit msg") is True
    assert Git.check_commit_message("feat!: test commit msg") is True
    assert Git.check_commit_message("feat(api)!: test commit msg") is True
    assert Git.check_commit_message("build: test commit msg") is True
    assert Git.check_commit_message("chore: test commit msg") is True
    assert Git.check_commit_message("ci: test commit msg") is True
    assert Git.check_commit_message("docs: test commit msg") is True
    assert Git.check_commit_message("style: test commit msg") is True
    assert Git.check_commit_message("refactor: test commit msg") is True
    assert Git.check_commit_message("perf: test commit msg") is True
    assert Git.check_commit_message("test: test commit msg") is True
    assert Git.check_commit_message("test:test commit msg") is True
    assert Git.check_commit_message("BREAKING CHANGE: test commit msg") is True
    assert Git.check_commit_message("Breaking change: test commit msg") is True
    assert Git.check_commit_message("deprecated: test commit msg") is True
    assert Git.check_commit_message("deprecated(api): test commit msg") is True
    assert Git.check_commit_message("test commit msg") is False
    assert Git.check_commit_message("test:") is False
    assert Git.check_commit_message("test:   ") is False
    assert Git.check_commit_message("feat: test, BREAKING CHANGE: test commit msg") is True
    assert Git.check_commit_message("feat: test, \nBREAKING CHANGE: test commit msg") is True
    assert Git.check_commit_message("feat: test, Breaking change: test commit msg") is True
    assert Git.check_commit_message("feat: test, \nBreaking change: test commit msg") is True
    assert Git.check_commit_message("Merge branch 'test/test-rebase-2' into test/test-rebase-1") is True
    assert Git.check_commit_message("Merge branch-'test/test-rebase-2' into test/test-rebase-1") is False
    assert Git.check_commit_message(" Merge branch 'test/test-rebase-2' into test/test-rebase-1") is False
    assert Git.check_commit_message("Merge pull request 'test/test-rebase-2' into test/test-rebase-1") is True
    assert Git.check_commit_message("Merge pull request-'test/test-rebase-2' into test/test-rebase-1") is False
    assert Git.check_commit_message(" Merge pull request'test/test-rebase-2' into test/test-rebase-1") is False


def test_commit_msg_normalize():
    assert Git._commit_msg_normalize("fix: test ") == "test"
    assert Git._commit_msg_normalize("fix: test") == "test"
    assert Git._commit_msg_normalize("fix:test") == "test"
    assert Git._commit_msg_normalize("test") == "test"
    assert Git._commit_msg_normalize(" test ") == "test"


def test_changelog_group_sort():
    expected = {
        'features': [
            'feat(api)!: new api'
        ],
        'bugfixes': [
            'fix: test fix 1',
            'fix(api)!: test fix 2'
        ],
        'deprecations': [],
        'others': [],
        'docs': [],
        'non_conventional_commit': []
    }
    res = Git._changelog_group_sort(git_log="feat(api)!: new api\n"
                                            "fix: test fix 1\n"
                                            "fix(api)!: test fix 2",
                                    commit_wo_prefix=False,
                                    unique=True
                                    )
    assert expected == res["changelog"]

    expected = {
        'features': [
            'new api'
        ],
        'bugfixes': [
            'test fix 1',
            'test fix 2'
        ],
        'deprecations': [],
        'others': [],
        'docs': [],
        'non_conventional_commit': []
    }
    res = Git._changelog_group_sort(git_log="feat(api)!: new api\n"
                                            "fix: test fix 1\n"
                                            "fix(api)!: test fix 2",
                                    commit_wo_prefix=True,
                                    unique=True
                                    )
    assert expected == res["changelog"]


def test_changelog_group_bump_version():
    # Patch
    res = Git._changelog_group_sort(git_log="chore: test update 1\n",
                                    commit_wo_prefix=False,
                                    unique=True
                                    )
    expected_bump_rules = {'major': False, 'minor': False, 'patch': True}
    assert expected_bump_rules == res["bump_rules"]

    res = Git._changelog_group_sort(git_log="fix: test update 1\n",
                                    commit_wo_prefix=False,
                                    unique=True
                                    )
    expected_bump_rules = {'major': False, 'minor': False, 'patch': True}
    assert expected_bump_rules == res["bump_rules"]

    res = Git._changelog_group_sort(git_log="docs: remove deprecated docs 1\n",
                                    commit_wo_prefix=False,
                                    unique=True
                                    )
    expected_bump_rules = {'major': False, 'minor': False, 'patch': True}
    assert expected_bump_rules == res["bump_rules"]

    res = Git._changelog_group_sort(git_log="non conventional commit\n",
                                    commit_wo_prefix=False,
                                    unique=True
                                    )
    expected_bump_rules = {'major': False, 'minor': False, 'patch': True}
    assert expected_bump_rules == res["bump_rules"]

    # Minor
    res = Git._changelog_group_sort(git_log="feat(api): update response\n"
                                            "fix: test fix 1\n",
                                    commit_wo_prefix=False,
                                    unique=True
                                    )
    expected_bump_rules = {'major': False, 'minor': True, 'patch': True}
    assert expected_bump_rules == res["bump_rules"]

    # Major
    res = Git._changelog_group_sort(git_log="feat(api)!: new api", commit_wo_prefix=False, unique=True)
    assert res["bump_rules"]["major"]

    res = Git._changelog_group_sort(git_log="fix(api)!: new api", commit_wo_prefix=False, unique=True)
    assert res["bump_rules"]["major"]

    res = Git._changelog_group_sort(git_log="breaking change: api", commit_wo_prefix=False, unique=True)
    assert res["bump_rules"]["major"]

    res = Git._changelog_group_sort(git_log="deprecated: api", commit_wo_prefix=False, unique=True)
    assert res["bump_rules"]["major"]

    res = Git._changelog_group_sort(git_log="fix: api, breaking change: remove api endpoint", commit_wo_prefix=False,
                                    unique=True)
    assert res["bump_rules"]["major"]

    # No update
    res = Git._changelog_group_sort(git_log="", commit_wo_prefix=False, unique=True)
    expected_bump_rules = {'major': False, 'minor': False, 'patch': False}
    assert expected_bump_rules == res["bump_rules"]
