#!/usr/bin/env bash
set -e

###############################################################################
#
#   xss-commit-linter.sh
#
#   Executes xsslint/xss_linter.py on the set of files in a particular git commit.
#
###############################################################################

show_help() {
    echo "Usage: xss-commit-linter.sh [OPTION]"
    echo "Runs the XSS Linter against all files in a git commit."
    echo ""
    echo "Mandatory arguments to long options are mandatory for short options too."
    echo "  -h, --help                  Output this help."
    echo "  -m, --main-branch=COMMIT    Run against files changed between the"
    echo "                              current branch and this commit."
    echo "                              Defaults to origin/master."
    echo "  -v, --verbose               Output details of git commands run."
    echo ""
    echo "This scripts does not give a grand total.  Be sure to check for"
    echo "0 violations on each file."
    echo ""
    echo "For more help using the xss linter, including details on how to"
    echo "understand and fix any violations, read the docs here:"
    echo ""
    echo "  https://edx.readthedocs.io/projects/edx-developer-guide/en/latest/preventing_xss/index.html"

}

show_verbose() {
    echo "Files linted is based on the following:"
    echo "- Current commit: ${current_branch_hash}"
    echo "- Main commit: ${MAIN_COMMIT}"
    echo "- Merge base command: ${merge_base_command}"
    echo "- Merge base: ${merge_base}"
    echo "- Diff command: ${diff_command}"

}

for i in "$@"; do
    case $i in
        -m=*|--main-branch=*)
            MAIN_COMMIT="${i#*=}"
            shift # past argument=value
            ;;
        -v|--verbose)
            VERBOSE=true
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
    if [ -z ${TARGET_BRANCH+x} ]; then
        # if commit is not set and no target branch, get hash of current branch
        MAIN_COMMIT="origin/master"
    else
        if [[ $TARGET_BRANCH == origin/* ]]; then
            MAIN_COMMIT=$TARGET_BRANCH
        else
            MAIN_COMMIT=origin/$TARGET_BRANCH
        fi
    fi
fi

merge_base_command="git merge-base $current_branch_hash $MAIN_COMMIT"
merge_base=$(${merge_base_command})
diff_command="git diff --name-only --diff-filter=ACM $merge_base $current_branch_hash"
diff_files=$(${diff_command})

if [ "$diff_files" = "" ]; then
    # When no files are found, automatically display verbose details to help
    # understand why.
    show_verbose
    echo ""
    echo "No files linted."
else
    if [ ${VERBOSE} ] ; then
        show_verbose
    fi
    for f in $diff_files; do
        echo ""
        echo "Linting $f:"
        ./scripts/xsslint/xss_linter.py --config=scripts.xsslint_config $f
    done
fi
