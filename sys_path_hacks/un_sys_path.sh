#!/usr/bin/env bash
# Example usage:
#   ~/edx-platform> sys_path_hacks/un_sys_path.sh lms
#   Writing sys_path_hacks/lms/.../xyz.py
#   ....
#   ~/edx-platform>

# Shellcheck recommends using search/replace instead of sed. It's fine as is.
# shellcheck disable=SC2001

set -e
set -o pipefail
set -u

TARGET="$1"
for path in $(find "${TARGET}/djangoapps/" -name '*.py' | grep -v migrations); do
    if [[ "$path" == "${TARGET}/djangoapps/__init__.py" ]]; then
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
    new_path=$(echo "$path" | sed "s#${TARGET}/djangoapps/#sys_path_hacks/${TARGET}/#")
    python_path=$(echo "$path" | sed "s#/#.#g" | sed "s#.py##" | sed "s#.__init__##")
    old_python_path=$(echo "$python_path" | sed "s#${TARGET}.djangoapps.##")
    echo "Writing ${new_path}"
    mkdir -p "$(dirname "$new_path")"
    {
        echo "from sys_path_hacks.warn import warn_deprecated_import"
        echo
        echo "warn_deprecated_import('${TARGET}.djangoapps', '${old_python_path}')"
        echo
        echo "from ${python_path} import *" 
    } > "$new_path"
done
