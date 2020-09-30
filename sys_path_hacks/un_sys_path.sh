#!/usr/bin/env bash
#
# Usage:
#
#   sys_path_hacks/un_sys_path.sh SOURCE DESTINATION
#    
#      where SOURCE is the folder from which modules will be recursively copied
#      and DESTINATION is the subfolder of `sys_path_hacks` in which they end up.
#   
# For example:
# 
#      ~/edx-platform> sys_path_hacks/un_sys_path.sh common/djangoapps studio
#    
#      will mirror the packages structure of `common/djangoapps` within `sys_path_hacks/studio`.
#      One would run this if they want to mimic the effect of adding 'common/djangoapps'
#      to `sys.path` within Studio.

# Shellcheck recommends using search/replace instead of sed. It's fine as is.
# shellcheck disable=SC2001

set -e
set -o pipefail
set -u

SOURCE="$1"
PYTHON_SOURCE="${SOURCE/\//.}"
DESTINATION="$2"
for path in $(find "${SOURCE}/" -name '*.py' | grep -v migrations); do
    if [[ "$path" == "${SOURCE}/__init__.py" ]]; then
        # Skip unnecessary root __init__.py.
        continue
    fi
    if [[ "$path" == "lms/djangoapps/courseware/management/commands/import.py" ]]; then
        # Skip this file because its name is problematic for the sys path hack.
        # We've gone to prod with this excluded, and it hasn't been a problem.
        continue
    fi
    if [[ "$path" == "cms/djangoapps/contentstore/management/commands/import.py" ]]; then
        # Also skip this file because its name is problematic for the sys path hack.
        continue
    fi
    new_path=$(echo "$path" | sed "s#${SOURCE}/#sys_path_hacks/${DESTINATION}/#")
    python_path=$(echo "$path" | sed "s#/#.#g" | sed "s#.py##" | sed "s#.__init__##")
    old_python_path=$(echo "$python_path" | sed "s#${PYTHON_SOURCE}.##")
    echo "Writing ${new_path}"
    mkdir -p "$(dirname "$new_path")"
    {
        echo "from sys_path_hacks.warn import warn_deprecated_import"
        echo
        echo "warn_deprecated_import('${PYTHON_SOURCE}', '${old_python_path}')"
        echo
        echo "from ${python_path} import *" 
    } > "$new_path"
done
