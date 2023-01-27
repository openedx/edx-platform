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
                                             Defaults to ./node_modules.\n\
    -L, --skip-lms                           Don't compile LMS-specific SCSS.\n\
    -C, --skip-cms                           Don't compile CMS-specific SCSS.\n\
    -D, --skip-default-theme                 Don't compile SCSS for the default theme.\n\
    -n, --node-modules <NODE_MODULES_PATH>   Path to installed node_modules directory.\n\
    -f, --force                              Remove existing css before generating new css\n\
    -d, --dev                                Dev mode: Don't compress output CSS\n\
    -r, --dry                                Dry run: don't do anything; just print what _would_ be done.\n\
    -v, --verbose                            Print commands as they are executed.\n\
    -h, --help                               Display this.\n\
"

# List of paths to custom themes, newline-separated.
theme_paths=""

# By default, we look for node_modules in the current directory.
# Some Open edX distributions may want node_modules to be located somewhere
# else, so we let this be configured with -n|--node-modules.
node_modules_path="./node_modules"

# Flags.
#  Empty string    (-z) => false
#  Nonempty string (-n) => true
skip_lms=""
skip_cms=""
skip_default_theme=""
force=""
dev=""
verbose=""
dry=""

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
		-f|--force)
			force="T"
			shift
			;;
		-d|--dev)
			dev="T"
			shift
			;;
		-v|--verbose)
			verbose="T"
			shift
			;;
		-r|-dry)
			dry="T"
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

	scss_src="$1"      # Dir containing SCSS input files.
	css_dest="$2"      # Target dir for CSS output, to mirror input dir structure.
	include_paths="$3" # List of SCSS import root paths, colon-separated.

	if [ ! -d "$scss_src" ] ; then
		echo "Directory $scss_src does not exist; skipping."
		return
	fi

	# TODO: This will fail if any of the paths have spaces in them, because such a path
	#       would be parsed as multiple arguments rather than one argument with a space
	#       inside it.
	compile_scss_dir_command="/bin/sh scripts/assets/compile-scss-dir.sh $scss_src $css_dest $include_paths"
	if [ -n "$dev" ] ; then
		compile_scss_dir_command="$compile_scss_dir_command --dev"
	fi
	if [ -n "$verbose" ] ; then
		compile_scss_dir_command="$compile_scss_dir_command --verbose"
	fi

	echo "Compiling directory: $scss_src -> $css_dest ..."
	if [ -n "$force" ] ; then
		echo " Removing old contents of $css_dest."
		[ -z "$dry" ] && rm -f "$css_dest/*.css"
	fi
	# shellcheck disable=2086
	[ -z "$dry" ] && \
		$compile_scss_dir_command
	echo " Done compiling: $scss_src -> $css_dest."
}

echo "-------------------------------------------------------------------------"
echo "  Compiling SCSS..."
echo
echo "  Working directory     : $(pwd)"
echo "-------------------------------------------------------------------------"

common_include_paths=\
"common/static\
:common/static/sass\
:$node_modules_path\
:$node_modules_path/@edx\
"
lms_include_paths=\
"$common_include_paths\
:lms/static/sass\
:lms/static/sass/partials\
"
cms_include_paths=\
"$common_include_paths\
:cms/static/sass\
:cms/static/sass/partials\
:lms/static/sass/partials\
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
	echo "Done compiling SCSS for default theme."
fi

echo "$theme_paths" | while read -r theme_path ; do

	if [ -z "$theme_path" ] ; then
		continue
	fi

	echo "Compiling SCSS for custom theme at $theme_path..."

	theme_lms_include_paths=\
"$lms_include_paths\
:$theme_path/lms/static/sass/partials\
"
	theme_certificate_include_paths=\
"$common_include_paths\
:$theme_path/lms/static/sass\
:$theme_path/lms/static/sass/partials\
"
	theme_cms_include_paths=\
"$cms_include_paths\
:$theme_path/cms/static/sass/partials\
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
echo "  Done compiling SCSS."
echo "-------------------------------------------------------------------------"

