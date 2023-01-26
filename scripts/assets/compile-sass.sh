#!/bin/sh
HELP="Compile SCSS files for LMS and CMS, including SCSS for zero or more themes."
#
# Run this from the root of edx-platform, after ... TOOD
# but before ... TODO

# Enable stricter sh behavior.
set -eu  

USAGE="\
USAGE:\n\
    $0 [OPTIONS]\n\
\n\
OPTIONS:\n\
	-t, --theme <THEME_PATH>                 Path to a custom theme. Can be provided multiple times.\n\
    -n, --node-modules <NODE_MODULES_PATH>   Path to installed node_modules directory.\n\
                                             Defaults to ./node_modules.\n\
    -w, --watch                              Watch SCSS directories and compile and recompile whenever changed\n\
    -L, --skip-lms                           Don't compile LMS-specific SCSS.\n\
    -C, --skip-cms                           Don't compile CMS-specific SCSS.\n\
    -D, --skip-default-theme                 Don't compile SCSS for the default theme.\n\
    -f, --force                              Remove existing css before generating new css\n\
    -d, --dev                                Dev mode: whether to show source comments in resulting css\n\
    -r, --dry                                Dry run: don't do anything; just print what _would_ be done.\n\
	-v, --verbose                            Print commands as they are executed.\n\
    -h, --help                               Display this.\n\
"

# Commands we use.
# In --dry mode, these are overriden to 'echo <command>'
rm='rm'
sassc='sassc'
rtlcss='echo rtlcss'  # TODO change

# By default, we look for node_modules in the current directory.
# Some Open edX distributions may want node_modules to be located somewhere
# else, so we let this be configured with -n|--node-modules.
node_modules_path="./node_modules"

# List of paths to custom themes, newline-separated.
theme_paths=""

# Flags.
#  Empty string    (-z) => false
#  Nonempty string (-n) => true
skip_lms=""
skip_cms=""
skip_default_theme=""
force=""
watch=""
verbose=""

# Output style arguments, to be passed to underlying
# libsass complition command.
output_options="--output-style=compressed"

# Parse arguments and options.
while [ $# -gt 0 ]; do
	case $1 in
		-t|--theme)
			shift
			if [ $# -eq 0 ] || [ ! -d "$1" ]; then
				echo "Error: provided theme path is not a directory: ${1:-}"
				echo
				echo "$USAGE"
				exit 1
			fi 
			theme_paths="$theme_paths\n$1"
			shift
			;;
		-n|--node-modules)
			shift
			if [ $# -eq 0 ]; then
				echo "Error: Missing value for -n/--node-modules"
				echo
				echo "$USAGE"
				exit 1
			fi
			node_modules_path="$1"
			shift
			;;
		-w|--watch)
			watch="T"
			shift
			;;
		-L|--skip-lms)
			skip_lms="T"
			shift
			;;
		-C|--skip-cms)
			skip_cms="T"
			shift
			;;
		-D|--skip-default-theme)
			skip_default_theme="T"
			shift
			;;
		-f|--force)
			force="T"
			shift
			;;
		-d|--dev)
			output_options="--output-style=nested"
			# TODO: When moving from `sass.compile(...)` to `sassc`, we had to stop using
			#       the " --source-comments" option because it is not available
			#       in the `sassc` CLI under libsass==0.10. After upgrading to libsass>=0.11,
			#       we should add back " --source-comments" when in --dev mode.
			shift
			;;
		-r|-dry)
			rm="echo rm"
			sassc="echo sassc"
			rtlcss="echo rtlcss"
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
		*)
			echo "Error: Unrecognized option: $1"
			echo
			echo "$USAGE"
			exit 1
			;;
	esac
done

compile_dir ( ) {
	scss_src="$1"
	css_dest="$2"
	include_path_options="$3"

	echo "Compiling: $scss_src -> $css_dest ..."
	if [ ! -d "$scss_src" ] ; then
		echo "Directory $scss_src does not exist; skipping."
		return
	fi

	if [ -n "$force" ] ; then
		echo " Removing old contents of $css_dest."
		$rm -f "$css_dest/*.css"
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
		$sassc $output_options $include_path_options "$scss_src/$rel_path.scss" "$css_dest/$rel_path.css"

		# Generate converted RTL css too, if relevant.
		case "$rel_path" in
			*-rtl)
				# SCSS is already RTL; no need to generate extra RTL file.
				;;
			*)
				# Generate RTL CSS from LTR CSS, appending -rtl to file name.
		 		# shellcheck disable=2086
				$rtlcss "$css_dest/$rel_path.css" "$css_dest/$rel_path-rtl.css"
				;;
		esac
	done

	echo " Compiled: $scss_src -> $css_dest."
}
echo "-------------------------------------------------------------------------"
if [ -n "$watch" ] ; then
	echo "Watching SCSS for changes..."
	echo "ERROR: watching is not yet implemented"
	exit 1
else
	echo "Compiling SCSS..."
fi
echo "  Working directory     : $(pwd)"
echo "-------------------------------------------------------------------------"

common_include_paths=\
"--include-path=common/static\
 --include-path=common/static/sass\
 --include-path=$node_modules_path\
 --include-path=$node_modules_path/@edx\
"
lms_include_paths=\
"$common_include_paths\
 --include-path=lms/static/sass\
 --include-path=lms/static/sass/partials\
"
cms_include_paths=\
"$common_include_paths\
 --include-path=cms/static/sass\
 --include-path=cms/static/sass/partials\
 --include-path=lms/static/sass/partials\
"

if [ -n "$verbose" ] ; then
	set -x
fi

if [ -z "$skip_default_theme" ] ; then
	echo "Compiling SCSS for default theme..."
	if [ -z "$skip_lms" ] ; then
		compile_dir \
			"lms/static/sass" \
			"lms/static/css" \
			"$lms_include_paths"
		compile_dir \
			"lms/static/certificates/sass" \
			"lms/static/certificates/css" \
			"$lms_include_paths"
	fi
	if [ -z "$skip_cms" ] ; then 
		compile_dir \
			"cms/static/sass" \
			"cms/static/css" \
			"$cms_include_paths"
	fi
	echo "Default theme SCSS compiled."
fi

echo "$theme_paths" | while read -r theme_path ; do

	if [ -z "$theme_path" ] ; then
		continue
	fi

	echo "Compiling SCSS for custom theme at $theme_path..."

	theme_lms_include_paths=\
"$lms_include_paths\
 --include-path=$theme_path/lms/static/sass/partials\
"
	theme_certificate_include_paths=\
"$common_include_paths\
 --include-path=$theme_path/lms/static/sass\
 --include-path=$theme_path/lms/static/sass/partials\
"
	theme_cms_include_paths=\
"$cms_include_paths\
 --include-path=$theme_path/cms/static/sass/partials\
"
	if [ -z "$skip_lms" ] ; then
		# First, compile default LMS SCSS into theme's LMS CSS dir.
		compile_dir \
			"lms/static/sass"  \
			"$theme_path/lms/static/css" \
			"$theme_lms_include_paths"
		# Then, override some/all default LMS CSS by compiling theme's LMS SCSS.
		compile_dir \
			"$theme_path/lms/static/sass" \
			"$theme_path/lms/static/css" \
			"$theme_lms_include_paths"
		# Finally, compile the themed certificate SCSS into certificate CSS dir.
		compile_dir \
			"$theme_path/lms/static/certificates/sass" \
			"$theme_path/lms/static/certificates/css" \
			"$theme_certificate_include_paths"
	fi
	if [ -z "$skip_cms" ] ; then 
		# Process for CMS is same as LMS, except no certificates.
		compile_dir \
			"cms/static/sass"  \
			"$theme_path/cms/static/css" \
			"$theme_cms_include_paths"
		compile_dir \
			"$theme_path/cms/static/sass" \
			"$theme_path/cms/static/css" \
			"$theme_cms_include_paths"
	fi

	echo "Done compiling SCSS for custom theme at $theme_path."
done



echo "-------------------------------------------------------------------------"
echo "Done compiling SCSS."
echo "-------------------------------------------------------------------------"
