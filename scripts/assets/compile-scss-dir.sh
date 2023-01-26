#!/bin/sh
HELP="Recursively compile SCSS in one directory."

# Enable stricter sh behavior.
set -eu  

USAGE="\
USAGE:\n\
    $0 [OPTIONS] <SCSS_SRC> <CSS_DEST> [<INCLUDE_PATHS>] [OPTIONS]\n\
\n\
ARGUMENTS:\n\
    SCSS_SRC                           Source directory with SCSS\n\
	CSS_DEST                           Target directory for output CSS\n\
	INCLUDE_PATHS                      Colon-separated list of SCSS import roots\n\
\n\
OPTIONS:\n\
    -d, --dev                          Dev mode: don't compress output CSS\n\
    -h, --help                         Display this.\n\
    -v, --verbose                      Print commands as they are executed.\n\
"

scss_src=""
css_dest=""
include_paths=""
output_options="--output-style=compressed"

# Flags.
#  Empty string    (-z) => false
#  Nonempty string (-n) => true
verbose=""

# Parse arguments and options.
while [ $# -gt 0 ]; do
	case $1 in
		-d|--dev)
			output_options="--output-style=nested"
			# TODO: When moving from `sass.compile(...)` to `sassc`, we had to stop using
			#       the " --source-comments" option because it is not available
			#       in the `sassc` CLI under libsass==0.10. After upgrading to libsass>=0.11,
			#       we should add back " --source-comments" when in --dev mode.
			shift
			;;
		-v|--verbose)
			verbose="T"
			shift
			;;
		-h|--help)
			echo "$HELP"
			echo
			echo "$USAGE"
			exit 0
			;;
		-*)
			echo "Error: Unrecognized option: $1"
			echo
			echo "$USAGE"
			exit 1
			;;
		*)
			if [ -z "$scss_src" ] ; then
				scss_src="$1"
			elif [ -z "$css_dest" ] ; then
				css_dest="$1"
			elif [ -z "$include_paths" ] ; then
				include_paths="$1"
			else
				echo "Error: unexpected argument: $1"
				echo "$USAGE"
				exit 1
			fi
			shift
			;;
	esac
done

if [ -n "$verbose" ] ; then
	set -x
fi

if [ -z "$scss_src" ] || [ -z "$css_dest" ] ; then
	echo "Error: SCSS source dir and CSS destination dir are required."
	echo "$USAGE"
	exit 1
fi

# Convert include paths into string of options.
# Include paths are colon-separated, so we can replace the colons with ' --include-path='
# and then prepend one more '--include_path=' to the entire string, if nonempty.
include_path_options="$(echo "$include_paths" | sed -n 's/:/ --include-path=/pg')"
if [ -n "$include_path_options" ] ; then 
	include_path_options="--include-path=$include_path_options"
fi

# Navigate into `scss_src` and recursively print out relative paths for all SCSS
# files, excluding underscore-prefixed ones, using `sed` to chop off the file extension.
# For each filepath, run `sassc` and, if appropriate, `rtlcss`.
# TODO: Unlike its Python API, libsass-python's CLI does not support compiling entire
#       directories, so we must implement that logic ourselves. After we upgrade
#       to node-sass or dart-sass, though, this logic might be able to be simplified.
for rel_path in $(cd "$scss_src" && find . \( -name \*.scss -and \! -name _\* \) | sed -n 's/.scss$//p') ; do

	# Make sure the destination directory exists.
	mkdir -p "$(dirname "$css_dest/$rel_path")"

	# Compile one SCSS file into a CSS file.
	# Note that scssc's $..._options arguments are not quoted, because they
	# may contain multiple arguments, which we want to split apart rather than
	# pass as one big argument. Hence the shellcheck disable directive.
	# shellcheck disable=2086
	sassc $output_options $include_path_options "$scss_src/$rel_path.scss" "$css_dest/$rel_path.css"

	# Generate converted RTL css too, if relevant.
	case "$rel_path" in
		*-rtl)
			# SCSS is already RTL; no need to generate extra RTL file.
			;;
		*)
			# Generate RTL CSS from LTR CSS, appending -rtl to file name.
			rtlcss "$css_dest/$rel_path.css" "$css_dest/$rel_path-rtl.css"
			;;
	esac
done
