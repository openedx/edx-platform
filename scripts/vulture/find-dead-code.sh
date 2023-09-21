#!/usr/bin/env bash
set -e

############################################################################
#
# find-dead-code.sh
#
# This script analyzes the edx-platform for dead code instances using
# vulture, a static analysis tool that ranks potential unused code using
# the following confidence scores:
# - 100% = completely unreachable code: code that follows return, continue
#          or raise statements, or code that cannot logically be run, i.e.
#          a condition that can never be True
# - 90%  = unused imports within a file
# - 60%  = unused code: code that has no reference in the code base, aside
#          from definition
#
# This script will output a list of dead-code instances with their
# confidence scores, in descending order of the size of the instance
# (in lines). This in turn can be used to clean up the edx-platform.
# However, you shouldn't automatically delete code reported back from
# vulture. It can report false positives. Often it's not the case that
# code is truly dead, but has been referenced incorrectly (spelling)
# elsewhere in the code base, most likely in a refactor. Another example
# of code that will be interpreted as dead by vulture is anything that
# is used in a template (which is not considered in the analysis).
#
# Therefore, the results of this script should be used as a jumping off
# point for investigating potential dead code removal
#
############################################################################

OUTPUT_DIR="reports/vulture"
mkdir -p "$OUTPUT_DIR"
OUTPUT_FILE="${OUTPUT_DIR}/vulture-report.txt"
echo '' > "$OUTPUT_FILE"
# exclude test code from analysis, as it isn't explicitly called by other
# code. Additionally, application code that is only called by tests 
# should be considered dead
EXCLUSIONS='/test,/acceptance,cms/envs,lms/envs,/terrain,migrations/,signals.py'
MIN_CONFIDENCE=90
# paths to the code on which to run the analysis
CODE_PATHS=('cms' 'common' 'lms' 'openedx')
WHITELIST_PATH="$(dirname "${BASH_SOURCE[0]}")/whitelist.py"
echo "Checking for dead code in the following paths: ${CODE_PATHS[*]}"
echo "Results can be found in $OUTPUT_FILE"
vulture "${CODE_PATHS[@]}" "$WHITELIST_PATH" --exclude "$EXCLUSIONS" \
--min-confidence "$MIN_CONFIDENCE" \
--sort-by-size |tac > "$OUTPUT_FILE"
