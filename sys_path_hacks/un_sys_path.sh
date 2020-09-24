#! /bin/sh
export TARGET=$1
for path in $(find ${TARGET}/djangoapps/ -name '*.py' | grep -v migrations); do
    export new_path=$(echo $path | sed "s#${TARGET}/djangoapps/#sys_path_hacks/${TARGET}/#")
    export python_path=$(echo $path | sed "s#/#.#g" | sed "s#.py##" | sed "s#.__init__##")
    export old_python_path=$(echo $python_path | sed "s#${TARGET}.djangoapps.##")
    mkdir -p $(dirname $new_path)
    echo > $new_path <<SCRIPT
import warnings
import textwrap
warnings.warn(textwrap.dedent("""\
    Importing $old_python_path instead of $python_path is deprecated. See https://github.com/edx/edx-platform/blob/master/docs/decisions/0007-sys-path-modification-removal.rst.
""", stacklevel=2)

from $python_path import *
SCRIPT
done
