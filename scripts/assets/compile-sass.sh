#!/bin/sh
#
# Compile sass files.
#
# Run this from the root of edx-platform, after ... TOOD
# but before ... TODO

USAGE="\
USAGE:\n\
    $0 [OPTIONS]\n\
\n\
OPTIONS:\n\
    -n, --node_modules <NODE_MODULES_PATH>   Path to installed node_modules directory.\n\
                                             Defaults to ./node_modules.\n\
    --skip-lms                               Don't compile LMS-specific sass.\n\
    --skip-cms                               Don't compile CMS-specific sass.\n\
    -h, --help                               Display this.\n\
"

# By default, we look for node_modules in the current directory.
# Some Open edX distributions may want node_modules to be located somewhere
# else, so we let this be configured with -n|--node-modules.
NODE_MODULES_PATH="./node_modules"

# Source direcotires for LMS and CMS.
SASS_LOOKUP_PATHS_LMS="\
common/static \
common/static/sass \
$NODE_MODULES_PATH \
$NODE_MODULES_PATH/@edx"

SASS_LOOKUP_PATHS_CMS="\
$SASS_LOOKUP_PATHS_LMS \
lms/static/sass/partials"

# Flags for LMS and CMS compliation.
# Nonempty string (-n) means True.
# Empty string (-z) means False.
COMPILE_LMS="true"
COMPILE_CMS="true"

# Enable stricter sh behavior.
set -eu  

# Parse options.
while [ $# -gt 0 ]; do
	case $1 in
		-n|--node-modules)
			shift
			if [ $# -eq 0 ]; then
				echo "Error: Missing value for -n/--node-modules"
				echo "$USAGE"
				exit 1
			fi
			NODE_MODULES_PATH="$1"
			shift
			;;
		--skip-lms)
			COMPILE_LMS=""
			shift
			;;
		--skip-cms)
			COMPILE_CMS=""
			shift
			;;
		-h|--help)
			echo "$USAGE"
			exit 0
			;;
		*)
			echo "Error: Unrecognized option: $1"
			echo "$USAGE"
			exit 1
			;;
	esac
done

echo "-------------------------------------------------------------------------"
echo "Compiling sass..."
echo "  Working directory     : $(pwd)"
echo "  SASS_LOOKUP_PATHS_LMS : $SASS_LOOKUP_PATHS_LMS"
echo "  SASS_LOOKUP_PATHS_CMS : $SASS_LOOKUP_PATHS_CMS"
echo "  COMPILE_LMS           : ${COMPILE_LMS:-false}"
echo "  COMPILE_CMS           : ${COMPILE_CMS:-false}"
echo "-------------------------------------------------------------------------"

# Input validation
for lookup_path in $SASS_LOOKUP_PATHS_CMS $SASS_LOOKUP_PATHS_LMS ; do
	if ! [ -d "$lookup_path" ]; then
		echo "Error: not a directory: $lookup_path"
		exit 1
	fi
done

# Echo lines back to user.
set -x

echo TODO: implement

# Stop echoing.
set +x

echo "-------------------------------------------------------------------------"
echo "Done compiling sass."
echo "-------------------------------------------------------------------------"
