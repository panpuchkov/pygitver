#!/bin/sh
set -e

PYGITVER_ROOT="/pygitver"
GIT_HOOK_COMMIT_MSG_FILE_DST=".git/hooks/commit-msg"
GIT_HOOK_COMMIT_MSG_FILE_SRC="${PYGITVER_ROOT}/scripts/git/hooks/commit-msg"

echo "Installing git hook."

if [ ! -d ".git" ]; then
  echo "Directory '.git' not found. Run in the root directory of the repository." >&2
  exit 1
fi

if [ ! -e "${GIT_HOOK_COMMIT_MSG_FILE_DST}" ]; then
  PYGITVER_VERSION=$(pygitver --version | awk '{print $2}')
  sed "s|^COMMIT_LINT_DOCKER=\"panpuchkov/pygitver\"$|COMMIT_LINT_DOCKER=\"panpuchkov/pygitver:${PYGITVER_VERSION}\"|" \
      "${GIT_HOOK_COMMIT_MSG_FILE_SRC}" > "${GIT_HOOK_COMMIT_MSG_FILE_DST}"
  chmod +x "${GIT_HOOK_COMMIT_MSG_FILE_DST}"
  echo "Done. Hook pinned to panpuchkov/pygitver:${PYGITVER_VERSION}"
else
  echo "Git hook commit-msg already exists; please check if it is correct."
fi
