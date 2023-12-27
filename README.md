# pygitver

Features:
* Conventional Commit linter
* Generate CHANGELOG
* Bump version based on CHANGELOG

# Examples

You may use it as a Python package or a Docker container.

## PIP Package

```shell
$ git tag -l
v0.0.1
v0.0.2
$ pygitver --curr-ver
v0.0.2
$ pygitver --next-ver
v0.0.3

```


## Docker Container

```shell
$ git tag -l
v0.0.1
v0.0.2
$ docker run --rm -v $(pwd):/app -w /app --user "$(id -u):$(id -g)" panpuchkov/pygitver --curr-ver
v0.0.2
$ docker run --rm -v $(pwd):/app -w /app --user "$(id -u):$(id -g)" panpuchkov/pygitver --next-ver
v0.0.3
$ docker run --rm -v $(pwd):/app -w /app --user "$(id -u):$(id -g)" panpuchkov/pygitver changelog
##########
Change Log
##########

Version v0.0.3
=============

Features
--------

* Allow to trigger job manually

Bug Fixes
---------

* Path for the default changelog template

* Readme.md usage

Improved Documentation
----------------------

* Add examples to the readme.md

$ docker run --rm -v $(pwd):/app -w /app --user "$(id -u):$(id -g)" panpuchkov/pygitver changelog --format json | jq .
{
  "version": "v0.0.3",
  "bump_rules": {
    "major": false,
    "minor": false,
    "patch": true
  },
  "changelog": {
    "features": [
      "allow to trigger job manually"
    ],
    "bugfixes": [
      "path for the default changelog template",
      "README.md usage"
    ],
    "deprecations": [],
    "others": [],
    "docs": [
      "Add examples to the README.md"
    ],
    "non_conventional_commit": []
  }
}
$ docker run --rm -v $(pwd):/app -w /app --user "$(id -u):$(id -g)" panpuchkov/pygitver --help
usage: pygitver.py [-h] [-v] [-cv] [-nv] [-t] [-ccm CHECK_COMMIT_MESSAGE]
                   {changelog,changelogs} ...

pygitver tool, ver: 0.1.2

options:
  -h, --help            show this help message and exit
  -v, --version         show tool version
  -cv, --curr-ver       get current version (last git tag)
  -nv, --next-ver       get next version (bump last git tag)
  -t, --tags            git tags
  -ccm CHECK_COMMIT_MESSAGE, --check-commit-message CHECK_COMMIT_MESSAGE
                        check if the git commit message is valid for
                        Conventional Commits

Get changelog:
  {changelog,changelogs}
                        Get changelog in TEXT or JSON format
```

## Conventional Commits Rules
The tool supports simplified Conventional Commits, which are described in this section.

The commit message should be structured as follows:
```shell
<type>[optional scope]: <description>
```
 
The commit contains the following structural elements to communicate intent to the consumers of your library:
* `fix:` a commit of the type fix patches a bug in your codebase (this correlates with `PATCH` in Semantic Versioning).
* `feat:` a commit of the type feat introduces a new feature to the codebase (this correlates with `MINOR` in Semantic Versioning).
* `BREAKING CHANGE:` a commit that has a footer `BREAKING CHANGE:`, or appends a `!` after the type/scope, introduces a breaking API change (correlating with `MAJOR` in Semantic Versioning). A BREAKING CHANGE can be part of commits of any type.
* Other allowed prefixes: `build:`, `chore:`, `ci:`, `docs:`, `style:`, `refactor:`, `perf:`, `test:`. These correlate with `PATCH` in Semantic Versioning. 

### Conventional Commits Examples:

Commit without scope without breaking change.
```
fix: crash on wrong input data
```
 

Commit message with ! to draw attention to breaking change.
```
feat!: send an email to the customer when a product is shipped
```
 

Commit message with scope and ! to draw attention to breaking change.
```
feat(api)!: send an email to the customer when a product is shipped
```


Commit message with scope.
```
feat(lang): add Polish language
```


## Users (Developers) Section


### Install pygitver
Run in the `git` root folder of the target repository on localhost. 
```shell
docker run --rm -v $(pwd):/app -w /app --user "$(id -u):$(id -g)" --entrypoint '' panpuchkov/pygitver /pygitver/scripts/install.sh
```

* It doesn't matter what the current branch is.
* You should install it in every repository that needs conventional commit messages.

### Update pygitver

Run in a terminal in any folder:

```shell
docker pull panpuchkov/pygitver
```

### Usage

You don't need to use it directly; it will be used automatically on each git commit.

_Example of a commit message that is **NOT VALID** for Conventional Commits:_
```shell
$ git commit -am "test"
ERROR: Commit does not fit Conventional Commits requirements
```

_Example of a commit message that is **VALID** for Conventional Commits:_
```shell
$ git commit -am "feat: test"
[feature/test2 af1a5c4] feat: test
 1 file changed, 1 deletion(-)
```

_Note: repeat this procedure for each repository_

## DevOps and Tool Developers Section

### Usage

_**Note:** The tool is running in the docker container and mounting your repository. 
It means that you have to run it just from the repository's root directory, 
from the directory with `.git` folder._

```shell
docker run --rm -v $(pwd):/app -w /app panpuchkov/pygitver --help
```

#### Examples

Check if the git commit message is valid for Conventional Commits:
```shell
$ docker run --rm -v $(pwd):/app -w /app panpuchkov/pygitver --check-commit-message "feat: conventional commit message"
$ echo $? # get exit code
0
$ docker run --rm -v $(pwd):/app -w /app panpuchkov/pygitver --check-commit-message "non-conventional commit message"
ERROR: Commit does not fit Conventional Commits requirements
$ echo $? # get exit code
1
```

Get current version (last git tag):
```shell
$ docker run --rm -v $(pwd):/app -w /app --user "$(id -u):$(id -g)" panpuchkov/pygitver --curr-ver
v0.0.3
```

Get next version (bump last git tag):
```shell
$ docker run --rm -v $(pwd):/app -w /app --user "$(id -u):$(id -g)" panpuchkov/pygitver --next-ver
v1.0.0
```

#### Custom CHANGELOG Templates

* Take as an example: `./src/templates/changelog.tmpl`
* Place somewhere in your project custom template
* Send environment variable `PYGITVER_TEMPLATE_CHANGELOG` to docker 
  on run with full template path in Docker (usually `/app/...`)

### Development

#### Build Docker
```shell
docker build -t pygitver .
```

#### Install to Localhost
```shell
pip install -r requirements-dev.txt
```

#### Test on Localhost

##### Run all checks
```shell
tox
```

##### A single file of the test run
```shell
tox -e coverage -- ./tests/test_git.py -vv
```
or
```shell
coverage run -m pytest -- ./tests/test_git.py 
```

#### Build pip package

Linux
```shell
python3 -m build
```

For `Debian` based OS:
```shell
DEB_PYTHON_INSTALL_LAYOUT=deb_system python3 -m build
```
