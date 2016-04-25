#!/usr/bin/env bash
set -e

###############################################################################
#
#   safe-commit-linter.sh
#
#   Executes safe_template_linter.py on the set of files in a particular git
#   commit.
#
###############################################################################

show_help() {
    echo "Usage: safe-commit-linter.sh [OPTION]"
    echo "Runs the Safe Template Linter against all files in a git commit."
    echo ""
    echo "Mandatory arguments to long options are mandatory for short options too."
    echo "  -m, --main-branch=COMMIT    Run against files changed between the"
    echo "                              current branch and this commit."
    echo "                              Defaults to origin/master."
}

for i in "$@"; do
    case $i in
        -m=*|--main-branch=*)
            MAIN_COMMIT="${i#*=}"
            shift # past argument=value
            ;;
        -h|--help|*)
            # help or unknown option
            show_help
            exit 0
            ;;
    esac
done

current_branch_hash=`git rev-parse HEAD`

if [ -z "${MAIN_COMMIT+x}" ]; then
    # if commit is not set, get hash of current branch
    MAIN_COMMIT="origin/master"
fi

merge_base=`git merge-base "$current_branch_hash" "$MAIN_COMMIT"`
diff_files=`git diff --name-only "$current_branch_hash" "$merge_base"`

for f in $diff_files; do
    echo ""
    echo "Linting $f:"
    ./scripts/safe_template_linter.py $f
done
