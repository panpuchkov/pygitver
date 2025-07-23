import argparse

from pygitver.git import Git, GitError, CURRENT_VERSION_DEFAULT
from pygitver.changelogs_mngr import ChangelogsMngr, ChangelogsMngrError
import json


def main():
    parser = argparse.ArgumentParser(
        description=f"pygitver tool, ver: {Git.__version__}"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s " + Git.__version__,
        help="show tool version",
    )

    parser.add_argument(
        "-cv",
        "--curr-ver",
        action="store_true",
        help="get current version (last git tag)",
        required=False,
    )
    parser.add_argument(
        "-nv",
        "--next-ver",
        action="store_true",
        help="get next version (bump last git tag)",
        required=False,
    )
    parser.add_argument(
        "-t", "--tags", action="store_true", help="git tags", required=False
    )
    parser.add_argument(
        "-ccm",
        "--check-commit-message",
        action="store",
        help="check if the git commit message is valid for Conventional Commits",
        required=False,
    )

    # Changelog
    subparsers = parser.add_subparsers(
        title="Get changelog", help="Get changelog in TEXT or JSON format"
    )
    changelog = subparsers.add_parser("changelog")
    changelog.add_argument(
        "-s",
        "--start",
        type=str,
        default="",
        help="Starting from tag, default='last pygitver tag'",
    )
    changelog.add_argument(
        "-e", "--end", type=str, default="HEAD", help="Ending with tag, default=HEAD"
    )
    changelog.add_argument(
        "-f",
        "--format",
        type=str,
        default="text",
        help="Change log format (text, json), default=text",
    )
    # Changelog ^^^

    # Changelogs
    changelogs = subparsers.add_parser("changelogs")
    changelogs.add_argument(
        "-d",
        "--dir",
        type=str,
        required=True,
        help="Directory with microservices' changelog files",
    )
    changelogs.add_argument(
        "-clsv",
        "--changelogs-version",
        type=str,
        default="0.0.1",
        required=False,
        help="Directory with microservices' changelog files",
    )
    changelogs.add_argument(
        "-f",
        "--format",
        type=str,
        default="text",
        help="Change log format (text, json), default=text",
    )
    changelogs.add_argument(
        "-t",
        "--template",
        type=str,
        default="templates/changelog-common.tmpl",
        help="Template for the CHANGELOG in Jinja2 format",
    )
    # Changelogs ^^^

    args = parser.parse_args()

    try:
        if args.tags:
            for tag in Git.tags():
                print(tag)
        elif args.curr_ver:
            print(Git.version_current())
        elif args.next_ver:
            curr_ver = Git.version_current()
            if CURRENT_VERSION_DEFAULT == curr_ver:
                curr_ver = ""
            changelog_group = Git.changelog_group(start=curr_ver)
            print(changelog_group["version"])
        elif "dir" in args:
            join_changelogs = ChangelogsMngr(changelogs_version=args.changelogs_version)
            output = join_changelogs.read_files(path=args.dir, file_ext="json")
            if args.format == "text":
                try:
                    print(join_changelogs.generate(template_name=args.template))
                except ChangelogsMngrError as err:
                    print(err)
                    exit(1)
            elif args.format == "json":
                print(json.dumps(output))
            else:
                print("ERROR: unknown output format")
                exit(1)
        elif "format" in args:
            changelog_group = Git.changelog_group(
                start=args.start if args.start else Git.version_current(),
                end=args.end,
                unique=True,
            )
            if args.format == "text":
                print(Git.changelog_generate(changelog_group))
            elif args.format == "json":
                print(json.dumps(changelog_group))
            else:
                print("ERROR: unknown output format")
                exit(1)

    except GitError as err:
        git_error = json.loads(str(err))
        print(git_error["result"])
        exit(git_error["return_code"])

    if args.check_commit_message:
        res = Git.check_commit_message(args.check_commit_message)
        if not res:
            print("ERROR: Commit does not fit Conventional Commits requirements")
            print(
                "More about Conventional Commits: "
                "https://www.conventionalcommits.org/en/v1.0.0/"
            )
            exit(1)
    exit(0)


if __name__ == "__main__":
    main()
