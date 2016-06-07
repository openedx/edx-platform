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
    echo "  -h, --help                  Output this help."
    echo "  -m, --main-branch=COMMIT    Run against files changed between the"
    echo "                              current branch and this commit."
    echo "                              Defaults to origin/master."
    echo "  -v, --verbose               Output details of git commands run."
    echo ""
    echo "This scripts does not give a grand total.  Be sure to check for"
    echo "0 violations on each file."
    echo ""
    echo "For more help using the safe template linter, including details on how"
    echo "to understand and fix any violations, read the docs here:"
    echo ""
    echo "  http://edx.readthedocs.org/projects/edx-developer-guide/en/latest/conventions/safe_templates.html#safe-template-linter"

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
    # if commit is not set, get hash of current branch
    MAIN_COMMIT="origin/master"
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
        ./scripts/safe_template_linter.py $f
    done
fi
