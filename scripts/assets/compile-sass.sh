#!/bin/sh
#
# Compile sass files.
#
# Run this from the root of edx-platform, after ... TOOD
# but before ... TODO

# Enable stricter sh behavior.
set -eu  

USAGE="\
USAGE:\n\
    $0 [OPTIONS] common\n\
    $0 [OPTIONS] lms [<THEME_DIR>]\n\
    $0 [OPTIONS] cms [<THEME_DIR>]\n\
\n\
OPTIONS:\n\
    -n, --node_modules <NODE_MODULES_PATH>   Path to installed node_modules directory.\n\
                                             Defaults to ./node_modules.\n\
    -f, --force                              Remove existing css before generating new css\n\
    -d, --debug                              Whether to show source comments in resulting css\n\
    -h, --help                               Display this.\n\
"

# By default, we look for node_modules in the current directory.
# Some Open edX distributions may want node_modules to be located somewhere
# else, so we let this be configured with -n|--node-modules.
node_modules_path="./node_modules"

# system can be: lms, cms, or common.
# theme_dir can be a path, or empty.
# If sytem="common", then theme_dir should be empty.
system=""
theme_dir=""

# Should we delete css first? Default is false.
#  Empty string    (-z) => false
#  Nonempty string (-n) => true
force=""

# Output style arguments, to be passed to underlying
# libsass complition command.
source_comments="False"
output_style="compressed"

# Parse arguments and options.
while [ $# -gt 0 ]; do
	case $1 in
		-n|--node-modules)
			shift
			if [ $# -eq 0 ]; then
				echo "Error: Missing value for -n/--node-modules"
				echo "$USAGE"
				exit 1
			fi
			node_modules_path="$1"
			shift
			;;
		-f|--force)
			source_comments="True"
			output_style="nested"
			shift
			;;
		-d|--debug)
			source_comments="True"
			output_style="nested"
			shift
			;;
		-h|--help)
			echo "$USAGE"
			exit 0
			;;
		-*)
			echo "Error: Unrecognized option: $1"
			echo "$USAGE"
			exit 1
			;;
		*)  # Positional arguments. Can be supplied before, after, or between options.
			# First argument: system
			if [ -z "$system" ] ; then
				if [ "$1" = "lms" ] || [ "$1" = "cms" ] || [ "$1" = "common" ]; then
					system="$1"
				else
					echo "Error: expected lms, cms, or common: $1"
					echo "$USAGE"
					exit 1
				fi
			# Second argument: theme_dir
			elif [ -z "$theme_dir" ] ; then
				if [ "$system" = "common" ]; then
					echo "Error: cannot provide a theme when compiling common scss"
					echo "$USAGE"
					exit 1
				fi
				theme_dir="$1"
			# Three or more arguments is an error.
			else
				echo "Error: unexpected argument: $1"
				echo "$USAGE"
				exit 1
			fi
			shift
			;;
	esac
done

# Define source directories for LMS and CMS.
sass_lookup_paths_common="\
 common/static\
 common/static/sass\
 $node_modules_path\
 $node_modules_path/@edx"
sass_lookup_paths_cms="$sass_lookup_paths_common"
sass_lookup_paths_lms="$sass_lookup_paths_common lms/static/sass/partials"

# Input validation
if [ -z "$system" ]; then
	echo "Error: must specify lms, cms, or common."
	echo "$USAGE"
	exit 1
fi
if [ -n "$theme_dir" ] && ! [ -d "$theme_dir" ]; then
	echo "Error: provided theme directory is not a directory: $theme_dir"
	echo "$USAGE"
	exit 1
fi 
for lookup_path in $sass_lookup_paths_lms $sass_lookup_paths_cms; do
	if ! [ -d "$lookup_path" ]; then
		echo "Error: not a directory: $lookup_path"
		exit 1
	fi
done

echo "-------------------------------------------------------------------------"
echo "Compiling $system sass..."
echo "  Working directory     : $(pwd)"
echo "  sass_lookup_paths_lms :$sass_lookup_paths_lms"
echo "  sass_lookup_paths_cms :$sass_lookup_paths_cms"
echo "  node_modules_path     : $node_modules_path"
echo "  theme_dir             : $theme_dir"
echo "-------------------------------------------------------------------------"

# Echo lines back to user.
set -x

echo TODO: implement

# Stop echoing.
set +x

echo "-------------------------------------------------------------------------"
echo "Done compiling $system sass."
echo "-------------------------------------------------------------------------"
