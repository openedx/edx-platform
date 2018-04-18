#!/usr/bin/env bash
set -e

############################################################################
#
#   enumerate.sh
#
#   Enumerates all dependencies (imports) from Python modules in
#   edx-platform.  The resulting data file generated at
#   reports/dependencies/dependencies.txt can then be used by other scripts
#   to detect inappropriate imports, such as:
#
#   * Imports of test modules or testing packages from core application code
#   * Imports of development-only packages from core or test code
#   * Imports from a package we want to stop using as a dependency
#   * Imports of other edx-platform modules from a module we want to move to
#     a separate package in its own repository
#
#   This script can take a while to run (a few minutes), so it should be run
#   independently of the other scripts which use this data.
#
#   While running, a number of warnings such as "Could not import module
#   'assert_equal'" may be generated.  This is normal; the snakefood utility
#   can't really distinguish between the import of a module and the import of
#   an object within a module, so it prints a warning on all instances of the
#   latter just in case it actually was an attempt to import a module which
#   it couldn't find in the current PYTHONPATH.  If you do see some modules
#   listed which you think should be findable, you may need to run
#   "make requirements" or update the ROOTS variable in this script.
#
############################################################################

OUTPUT_DIR="reports/dependencies"
mkdir -p ${OUTPUT_DIR}
DEPENDENCIES=${OUTPUT_DIR}/dependencies.txt
ROOTS=cms/djangoapps:common/djangoapps:lms/djangoapps:scripts/xsslint
PYTHONPATH=${ROOTS} sfood cms common lms openedx pavelib scripts manage.py pavement.py > ${DEPENDENCIES}
