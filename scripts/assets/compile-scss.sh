#!/bin/sh
HELP="Compile SCSS files for LMS and CMS, for default and/or custom themes."
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
    -t, --theme <THEME_PATH>                 Path to a custom theme; can be provided multiple times\n\
    -L, --skip-lms                           Don't compile LMS-specific SCSS\n\
    -C, --skip-cms                           Don't compile CMS-specific SCSS\n\
    -D, --skip-default-theme                 Don't compile SCSS for the default theme\n\
    -n, --node-modules <NODE_MODULES_PATH>   Path to installed node_modules directory\n\
                                             Defaults to ./node_modules\n\
    -f, --force                              Remove existing css before generating new css\n\
    -d, --dev                                Dev mode: Don't compress output CSS\n\
    -r, --dry                                Dry run: don't actually execute any changes\n\
    -v, --verbose                            Print commands as they are executed\n\
    -h, --help                               Display this\n\
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
dry=""
verbose=""

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
		-r|--dry)
			dry="T"
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

compile_dir_opts=""
if [ -n "$dev" ] ; then
	compile_dir_opts="$compile_dir_opts --dev"
fi
if [ -n "$dry" ] ; then
	compile_dir_opts="$compile_dir_opts --dry"
fi
if [ -n "$verbose" ] ; then
	compile_dir_opts="$compile_dir_opts --verbose"
fi
compile_dir ( ) {
	# Shellcheck will complain that $compile_dir_opts is unquoted.
	# It's intentional: we want $compile_dir_opts to be split on spaces and
	# passed as multiple arguments. Quoting it would pass it as a single argument.
	# shellcheck disable=2086
	scripts/assets/compile-scss-dir.sh $compile_dir_opts "$1" "$2" "$3"
}

echo "-------------------------------------------------------------------------"
echo "  Compiling SCSS..."
echo
echo "  Working directory     : $(pwd)"
echo "-------------------------------------------------------------------------"


lms_scss="lms/static/sass"
lms_partials="lms/static/sass/partials"
cms_scss="cms/static/sass"
cms_partials="cms/static/sass/partials"
certs_scss="lms/static/certificates/sass"

lms_css="lms/static/css"
cms_css="cms/static/css"
certs_css="lms/static/certificates/css"

common_includes="common/static:common/static/sass:$node_modules_path:$node_modules_path/@edx"
lms_includes="$common_includes:$lms_scss:$lms_partials"
cms_includes="$common_includes:$cms_scss:$cms_partials:$lms_partials"
certs_includes="$lms_includes"

if [ -n "$verbose" ] ; then
	set -x
fi

if [ -z "$skip_default_theme" ] ; then
	echo "Compiling SCSS for default theme..."
	if [ -n "$force" ] ; then
		echo "  Removing existing generated CSS first."
		[ -n "$dry" ] || rm -rf "$lms_css" "$cms_css" "$certs_css"
	fi
	if [ -z "$skip_lms" ] ; then
		echo "  Compiling default LMS SCSS."
		compile_dir "$lms_scss" "$lms_css" "$lms_includes"
		echo "  Compiling default certificates SCSS."
		compile_dir "$certs_scss" "$certs_css" "$certs_includes"
	fi
	if [ -z "$skip_cms" ] ; then 
		echo "  Compiling default CMS SCSS."
		compile_dir "$cms_scss" "$cms_css" "$cms_includes"
	fi
	echo "Done compiling SCSS for default theme."
fi

echo "$theme_paths" | while read -r theme_path ; do

	if [ -z "$theme_path" ] ; then
		continue
	fi

	theme_lms_scss="$theme_path/lms/static/sass"
	theme_lms_partials="$theme_path/lms/static/sass/partials"
	theme_cms_scss="$theme_path/cms/static/sass"
	theme_cms_partials="$theme_path/cms/static/sass/partials"
	theme_certs_scss="$theme_path/lms/static/certificates/sass"

	theme_lms_css="$theme_path/lms/static/css"
	theme_cms_css="$theme_path/cms/static/css"
	theme_certs_css="$theme_path/lms/static/certificates/css"

	theme_lms_includes="$lms_includes:$theme_lms_partials"
	theme_cms_includes="$cms_includes:$theme_cms_partials"
	theme_certs_includes="$common_includes:$theme_lms_scss:$theme_lms_partials"

	echo "Compiling SCSS for custom theme at $theme_path..."
	if [ -n "$force" ] ; then
		echo "  Removing theme's existing generated CSS first."
		[ -n "$dry" ] || rm -rf "$theme_lms_css" "$theme_cms_css" "$theme_certs_css"
	fi

	if [ -z "$skip_lms" ] ; then
		echo "  Compiling default LMS SCSS into theme's CSS directory."
		compile_dir "$lms_scss" "$theme_lms_css" "$theme_lms_includes"
		if [ -d "$theme_lms_scss" ] ; then
			echo "  Compiling theme's LMS SCSS into theme's CSS directory."
			compile_dir "$theme_lms_scss" "$theme_lms_css" "$theme_lms_includes"
		else
			echo "  Theme has no LMS SCSS; skipping."
		fi
		if [ -d "$theme_certs_scss" ] ; then
			echo "  Compiling theme's certificate SCSS into theme's CSS directory."
			compile_dir "$theme_certs_scss" "$theme_certs_css" "$theme_certs_includes"
		else
			echo "  Theme has no certificate SCSS; skipping."
		fi
	fi
	if [ -z "$skip_cms" ] ; then 
		echo "  Compiling default CMS SCSS into theme's CSS directory."
		compile_dir "$cms_scss" "$theme_cms_css" "$theme_cms_includes"
		if [ -d "$theme_cms_scss" ] ; then
			echo "  Compiling theme's CMS SCSS into theme's CSS directory."
			compile_dir "$theme_cms_scss" "$theme_cms_css" "$theme_cms_includes"
		else
			echo "  Theme has no CMS SCSS; skipping."
		fi
	fi

	echo "Done compiling SCSS for custom theme at $theme_path."
done

echo "-------------------------------------------------------------------------"
echo "  Done compiling SCSS."
echo "-------------------------------------------------------------------------"

