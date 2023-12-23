import os
import json
from git import Git, GitError

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class ChangelogsMngrError(Exception):
    pass


class ChangelogsMngr:
    def __init__(self, changelogs_version: str = "0.0.1") -> None:
        self._changelogs_version = changelogs_version
        self._init_changelog()

    def _init_changelog(self):
        self._changelogs: dict = {"version": self._changelogs_version, "services": {}}
        self._bump_version_rules: dict = {
            "major": False,
            "minor": False,
            "patch": False,
        }

    def _update_bump_version_rules(self, service_name: str) -> None:
        for key in self._bump_version_rules.keys():
            self._bump_version_rules[key] |= self._changelogs["services"][service_name][
                "bump_rules"
            ][key]

    def read_files(self, path: str, file_ext: str = "json"):
        self._init_changelog()
        for file_name in sorted(os.listdir(path)):
            try:
                with open(os.path.join(path, file_name)) as fp:
                    if file_ext and file_name.endswith(f".{file_ext}"):
                        file_name = file_name[: -(len(file_ext) + 1)]
                    self._changelogs["services"][file_name] = json.load(fp)
                    self._update_bump_version_rules(file_name)
            except json.JSONDecodeError:
                # nothing to do, just skip invalid file
                pass
        try:
            self._changelogs["version"] = Git.bump_version(
                self._changelogs["version"],
                self._bump_version_rules,
            )
        except GitError:  # pragma: no cover
            self._changelogs["version"] = None
        return self._changelogs

    def changelog_generate(
        self, template_name: str = "templates/changelog-common.tmpl"
    ) -> str:
        try:
            env = Environment(loader=FileSystemLoader(os.path.dirname(template_name)))
            template = env.get_template(os.path.basename(template_name))
            output = template.render(**self._changelogs)
        except TemplateNotFound:
            raise ChangelogsMngrError(
                f"ERROR: Template '{template_name}' was not found."
            )
        return output
