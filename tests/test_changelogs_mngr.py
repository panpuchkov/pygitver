import os
import json
import unittest
from unittest import mock
from pygitver.changelogs_mngr import ChangelogsMngr, ChangelogsMngrError
from pygitver.git import Git


class TestChangelogsMngr(unittest.TestCase):

    @mock.patch.object(Git, "bump_current_version")
    def test_join_changelogs(self, monkeypatch):
        monkeypatch.return_value = "1.0.0"
        res = ChangelogsMngr().read_files("./tests/data/changelogs/", "json")
        with open("tests/data/joined_changelog.json", "r") as fp:
            expected = json.load(fp)
        assert res == expected

    @mock.patch.dict(os.environ, {"PYGITVER_TEMPLATE_CHANGELOG_COMMON": "src/pygitver/templates/changelog-common.tmpl"},
                     clear=True)
    def test_join_changelogs_template(self):
        join_changelogs = ChangelogsMngr("2.1.2")
        join_changelogs.read_files("./tests/data/changelogs/", "json")

        res = join_changelogs.generate()

        expected = "# Change Log\n\n" \
                   "## Version: 3.0.0\n\n\n\n\n\n" \
                   "## Services\n\n\n\n" \
                   "### Service-1\n\n" \
                   "Version: 1.2.0\n\n\n" \
                   "#### Features\n\n\n* Feat(api): new api 1.1\n\n* Feat(api): update api 1.2\n\n\n\n\n\n" \
                   "#### Bug Fixes\n\n\n* Fix: test fix 1\n\n\n\n\n\n" \
                   "#### Deprecations\n\n\n* Feat(api): deprecated 1\n\n\n\n\n" \
                   "#### Improved Documentation\n\n\n* Docs: update doc 1\n\n\n\n\n" \
                   "#### Trivial/Internal Changes\n\n\n* Refactor: code refactoring 1\n\n\n\n\n\n" \
                   "### Service-2\n\n" \
                   "Version: 2.0.0\n\n\n" \
                   "#### Features\n\n\n* Feat(api)!: new api 2\n\n\n\n\n\n" \
                   "#### Bug Fixes\n\n\n* Fix: test fix 2.1\n\n* Fix(api)!: test fix 2.2\n\n\n\n\n\n" \
                   "#### Deprecations\n\n\n* Feat(api): deprecated 2\n\n\n\n\n" \
                   "#### Improved Documentation\n\n\n* Docs: update doc 2\n\n\n\n\n" \
                   "#### Trivial/Internal Changes\n\n\n* Refactor: code refactoring 2\n\n\n\n"
        l_res = res.split("\n")
        l_expected = expected.split("\n")
        for pos, _ in enumerate(l_res):
            self.assertEqual(l_expected[pos], l_res[pos])

        res = join_changelogs.generate(template_name="src/pygitver/templates/changelog-common.tmpl")
        l_res = res.split("\n")
        l_expected = expected.split("\n")
        for pos, _ in enumerate(l_res):
            self.assertEqual(l_expected[pos], l_res[pos])

    def test_init_changelog(self):
        chl_mngr = ChangelogsMngr()
        chl_mngr._changelogs = {"version": "0.0.0", "services": {"test": None}}
        chl_mngr._bump_version_rules = {"major": True, "minor": True, "patch": True}
        chl_mngr._init_changelog()
        self.assertEqual(chl_mngr._changelogs, {"version": "0.0.1", "services": {}})
        self.assertEqual(chl_mngr._bump_version_rules, {"major": False, "minor": False, "patch": False})

    def test_changelog_generate(self):
        template_name = "no-template.tmpl"
        chl_mngr = ChangelogsMngr()

        with self.assertRaises(ChangelogsMngrError) as context:
            chl_mngr.generate(template_name=template_name)
        self.assertEqual(f"ERROR: Template '{template_name}' was not found.",
                         str(context.exception))
