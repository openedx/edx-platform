#!/usr/bin/env bash
# Example usage:
#   ~/edx-platform> sys_path_hacks/un_sys_path.sh lms
#   Writing sys_path_hacks/lms/.../xyz.py
#   ....
#   ~/edx-platform>

set -e
set -o pipefail
set -u

export TARGET="$1"
for path in $(find "${TARGET}/djangoapps/" -name '*.py' | grep -v migrations); do
    export new_path=$(echo "$path" | sed "s#${TARGET}/djangoapps/#sys_path_hacks/${TARGET}/#")
    export python_path=$(echo "$path" | sed "s#/#.#g" | sed "s#.py##" | sed "s#.__init__##")
    export old_python_path=$(echo "$python_path" | sed "s#${TARGET}.djangoapps.##")
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
