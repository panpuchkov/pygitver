#!/bin/sh

PYGITVER_ROOT="/pygitver"
GIT_HOOK_COMMIT_MSG_FILE_DST=".git/hooks/commit-msg"
GIT_HOOK_COMMIT_MSG_FILE_SRC="${PYGITVER_ROOT}/scripts/git/hooks/commit-msg"

echo "Installing git hook.";
if [ ! -r ".git" ]; then
  echo "Directory '.git' not found. Run in the root directory of the repository."
fi

if [ ! -r "${GIT_HOOK_COMMIT_MSG_FILE_DST}" ]; then
  cp "${GIT_HOOK_COMMIT_MSG_FILE_SRC}" ${GIT_HOOK_COMMIT_MSG_FILE_DST}
  chmod +x ${GIT_HOOK_COMMIT_MSG_FILE_DST}
  echo "Done."
else
  echo "Git hook commit-msg is already exists, please check if it is correct."
fi
