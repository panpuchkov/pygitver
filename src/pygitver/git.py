import json
import os
import re
import subprocess
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class GitError(Exception):
    pass


RE_CONVENTIONAL_COMMIT = (
    r"^("
    r"(?:"
    r"(?:(?:fix)|(?:feat)|(?:build)|(?:chore)|(?:ci)|(?:docs)|(?:style)|(?:refactor)|(?:perf)|(?:test)|(?:deprecated)"
    r"|(?:BREAKING CHANGE))"
    r"[\s\t]*(?:\([^\:)]+\))?[\s\t]*!?:[\s\t]*"
    r")"
    r"|(?:Merge branch )|(?:Merge pull request )"
    r")"
)


class Git:
    __version__ = "0.1.2"

    @staticmethod
    def _cmd(command: str) -> str:
        """
        Run shell command, used for running git commands.

        :param command: string with shell command
        :return: string with the raw output of the shell stdout
        """
        subprocess_res = subprocess.run(
            list(filter(lambda x: x, command.split(" "))),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        output = subprocess_res.stdout.decode("utf-8")
        if 0 != subprocess_res.returncode:
            raise GitError(
                json.dumps({"return_code": subprocess_res.returncode, "result": output})
            )  # pragma: no cover
        return output

    @classmethod
    def _commit_msg_normalize(cls, commit: str) -> str:
        """
        Normalize commit message, removes pygitver prefix from git commit,
            example: "fix: commit message" -> "commit message".

        :param commit: string with the commit message
        :return: string with the normalized commit message
        """
        return (
            re.sub(RE_CONVENTIONAL_COMMIT, "", commit, flags=re.IGNORECASE)
            .rstrip()
            .lstrip()
        )

    @staticmethod
    def _append_commit_to_section(
        section: list, _commit_normalized: str, _unique: bool
    ) -> None:
        """
        Append commit to the required section.

        :param section: target section where to add a commit message
            (normalized or as is)
        :param _commit_normalized: Normalize commit message if True
        :param _unique: do not add duplicates if is True
        """
        if _unique:
            if _commit_normalized not in section:
                section.append(_commit_normalized)
        else:
            section.append(_commit_normalized)

    @classmethod
    def _changelog_group_sort(
        cls, git_log: str, commit_wo_prefix: bool, unique: bool
    ) -> dict:
        """
        Sort change log by groups (features, bugfixes, deprecations, docs,
        others).

        :param git_log: multiline string with commits (one line per
            commit)
        :param unique: do not show duplicates commit if True
        :param commit_wo_prefix: remove commit pygitver prefix if is True
        :return: dict with commits sorted by groups and 'bump_rules',
            example: { "bump_rules": {"major": False, "minor": True,
            "patch": True}, "changelog": { 'features': [ 'feat(api)!:
            new api' ], 'bugfixes': [ 'fix: test fix 1', 'fix(api)!:
            test fix 2' ], 'deprecations': [], 'others': [], 'docs': [],
            'non_conventional_commit': [] } }
        """
        res: dict = {
            "features": [],
            "bugfixes": [],
            "deprecations": [],
            "others": [],
            "docs": [],
            "non_conventional_commit": [],
        }
        bump_rules: dict = {"major": False, "minor": False, "patch": False}
        for commit in git_log.rstrip().split("\n"):
            commit = commit.rstrip()
            commit_normalized = (
                cls._commit_msg_normalize(commit) if commit_wo_prefix else commit
            )
            if bool(
                re.search(
                    r"(^.*!:.+)|(^breaking change)|(^deprecated.*)|(.*:.*breaking change:.*)",
                    commit,
                    re.IGNORECASE,
                )
            ):
                bump_rules["major"] = True

            if bool(re.search("^deprecated.*:", commit, re.IGNORECASE)):
                cls._append_commit_to_section(
                    res["deprecations"], commit_normalized, unique
                )
            elif bool(re.search("^feat.*:", commit, re.IGNORECASE)):
                cls._append_commit_to_section(
                    res["features"], commit_normalized, unique
                )
                bump_rules["minor"] = True
            elif bool(re.search("^fix.*:", commit, re.IGNORECASE)):
                cls._append_commit_to_section(
                    res["bugfixes"], commit_normalized, unique
                )
                bump_rules["patch"] = True
            elif bool(re.search("^docs.*:", commit, re.IGNORECASE)):
                cls._append_commit_to_section(res["docs"], commit_normalized, unique)
                bump_rules["patch"] = True
            elif not bool(re.search(RE_CONVENTIONAL_COMMIT, commit, re.IGNORECASE)):
                cls._append_commit_to_section(
                    res["non_conventional_commit"], commit_normalized, unique
                )
                bump_rules["patch"] = True
            else:
                cls._append_commit_to_section(res["others"], commit_normalized, unique)
                bump_rules["patch"] = True
        return {"bump_rules": bump_rules, "changelog": res}

    @staticmethod
    def _version_prefix(version: str) -> str:
        """
        Get version prefix if exists, example version "v1.0.0", the prefix is
        "v".

        :param version: string with version
        :return: string with prefix, empty string if no prefix
        """
        search_res = re.search(r"^[^0-9]*", version)
        version_prefix = search_res.group() if search_res and search_res else ""
        return version_prefix

    @classmethod
    def tags(cls, update_from_remote: bool = False):
        """
        Get git tags sorted in back order.

        :param update_from_remote: run git fetch from remote before
            getting tags
        :return: string with git tags
        """
        if update_from_remote:  # pragma: no cover
            cls._cmd("git fetch --all --tags")
        branch = cls._cmd("git branch --show-current").strip("\r").strip("\n")
        res = list(
            filter(
                None,
                cls._cmd(f"git tag -l --sort=-v:refname --merged {branch}").split("\n"),
            )
        )
        return res

    @classmethod
    def check_commit_message(cls, commit: str) -> bool:
        """
        Check if the git commit message is valid for Conventional Commits.

        :param commit: git commit message
        :return: True if message is valid for Conventional Commits
        """
        return bool(
            re.match(f"{RE_CONVENTIONAL_COMMIT}([^\\s\\t]+)", commit, re.IGNORECASE)
        )

    @classmethod
    def changelog(cls, start: str = "", end: str = "") -> str:
        """
        Get raw change log from the 'start' to the 'end' steps.

        :param start: from git tag
        :param end: to git tag of HEAD by default
        :return: string with raw git log commit messages
        """
        if not start:
            start = cls._cmd("git log --pretty=format:%H --reverse -n 1")
        if not end:
            end = "HEAD"
        git_commits_range = (
            f"{start}...{end} " if "" != cls.version_current() else ""
        )  # pragma: no cover
        return cls._cmd(
            f"git log --pretty=format:%s {git_commits_range}--no-merges"
        )  # pragma: no cover

    @classmethod
    def changelog_group(
        cls,
        start: str = "",
        end: str = "HEAD",
        commit_wo_prefix: bool = True,
        unique: bool = False,
    ) -> dict:
        """
        Get raw change log from the 'start' to the 'end' steps.

        :param start: from git tag
        :param end: to git tag of HEAD by default
        :param commit_wo_prefix: remove commit pygitver prefixes if True
        :param unique: do not show duplicates commit if True
        :return: dict{"return_code": code, "result": {"fix": [], "feat":
            [], "other": []}}
        """
        git_log = cls.changelog(start=start, end=end)
        git_log_sorted = cls._changelog_group_sort(
            git_log, commit_wo_prefix, unique=unique
        )
        ver = (
            cls.bump_current_version(git_log_sorted["bump_rules"])
            if end == "HEAD"
            else end
        )
        return {"version": ver, **git_log_sorted}

    @staticmethod
    def changelog_generate(changelog_group: dict, template_name: str = "") -> str:
        """
        Generate full changelog.

        :param changelog_group: dictionary with changelog (result of the
            function 'changelog_group')
        :param template_name: file name with changelog template in
            Jinja2 format
        :return: string with formatted changelog
        """
        if not template_name:
            template_name = os.getenv(
                "PYGITVER_TEMPLATE_CHANGELOG", "templates/changelog.tmpl"
            )
        try:
            env = Environment(loader=FileSystemLoader(os.path.dirname(template_name)))
            template = env.get_template(os.path.basename(template_name))
            output = template.render(
                {"version": changelog_group["version"], **changelog_group["changelog"]}
            )
        except TemplateNotFound:
            output = f"ERROR: Template '{template_name}' was not found."
        return output

    @classmethod
    def git_version(cls) -> str:
        """
        Get installed git version.

        :return: string with git version
        """
        res = cls._cmd("git --version")
        res = res.replace("\n", "").split(" ")[-1]
        return res

    @classmethod
    def version_current(cls) -> str:
        """
        Get current (latest) git tag.

        :return: string with git tag or empty string if does not exist
        """
        for _tag in cls.tags():
            if cls.version_validate(_tag):
                return _tag
        return "0.0.0"

    @staticmethod
    def version_validate(version: str) -> bool:
        """
        Validate version string.

        :param version: string with version
        :return: True if version has correct format (example:
            'prefix1.2.3'), otherwise False
        """
        return bool(re.match(r"^[a-z\-_]*\d+\.\d+\.\d+(?:-[a-zA-Z\d.]+)?$", version))

    @classmethod
    def bump_current_version(cls, bump_rules: dict) -> str:
        """
        Get current version and bump is base on 'bump_rules' dict.

        :param bump_rules: bump version rules, example: {"major": False,
            "minor": True, "patch": False} version rules will be applied
            to the oldest (left to right) version rule with 'True'
        :return: string with the bumped current version
        """
        return cls.bump_version(cls.version_current(), bump_rules)

    @classmethod
    def bump_version(cls, version: str, bump_rules: dict) -> str:
        """
        Get current version and bump is base on 'bump_rules' dict.

        :param version: set new version if defined, otherwise take
            current
        :param bump_rules: bump version rules, example: {"major": False,
            "minor": True, "patch": False} version rules will be applied
            to the oldest (left to right) version rule with 'True'
        :return: string with the bumped current version
        """
        version_prefix = cls._version_prefix(version)
        version = version.removeprefix(version_prefix)

        version_items = version.split(".") if version != "" else ["0", "0", "0"]
        if bump_rules["major"] is True:
            version_items[0] = str(int(version_items[0]) + 1)
            version_items[1] = "0"
            version_items[2] = "0"
        elif bump_rules["minor"] is True:
            version_items[1] = str(int(version_items[1]) + 1)
            version_items[2] = "0"
        elif bump_rules["patch"] is True:
            # this case is covered by 'test_bump_version_auto', but not recognised by linter
            version_items[2] = str(int(version_items[2]) + 1)
        version = ".".join(version_items)
        return version_prefix + (version if version != "0.0.0" else "0.0.1")
