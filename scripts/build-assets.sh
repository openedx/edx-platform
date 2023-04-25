#!/usr/bin/env bash
ABOUT="Build static assets for edx-platform."

# Enable stricter error handling.
set -euo pipefail


#########################################################################
# ENVIRONMENT VARIABLES
#########################################################################

# Actual path to this script
THIS_SCRIPT="$0"

# Script name for logging & errors. Default to actual path.
SCRIPT_NAME="${SCRIPT_NAME:-$THIS_SCRIPT}"

# Default command line options.
# These are processed before any other command line options, so setting
# this environment variable is a way of setting custom 'default' values
# for this script. These defaults even show up in show_usage, because
# they are processed before --help is processed
# LIMITATION: Paths in arguments may not contain spaces. Quoting
# will not work.
DEFAULT_OPTS="${EDX_PLATFORM_BUILD_ASSETS_OPTS:-}"

# Extra fields to inject into the `process.env` of the Webpack build.
# Should be a valid JSON string representing an object.
# Defaults to empty object ('{}').
export JS_ENV_EXTRA_CONFIG="${JS_ENV_EXTRA_CONFIG:-{}}"


#########################################################################
# CONSTANTS
# Some of these are lowercase because they may become variables one day.
#########################################################################

# Codes for colored terminal output.
COL_LOG="\e[36m"  # Log/step/section color (cyan)
COL_RUN="\e[35m"  # Executed code echo color (purple)
COL_ERR="\e[31m"  # Error color (red)
COL_OFF="\e[0m"   # Normal color

# Input directories
node_modules="node_modules"
lms_scss="lms/static/sass"
cms_scss="cms/static/sass"
certs_scss="lms/static/certificates/sass"
lms_partials="lms/static/sass/partials"
cms_partials="cms/static/sass/partials"
common_includes=(
	"common/static"
	"common/static/sass"
	"$node_modules"
	"$node_modules/@edx"
)
lms_includes=(
	"${common_includes[@]}"
	"$lms_partials"
	"$lms_scss"
)
cms_includes=(
	"${common_includes[@]}"
	"$lms_partials"
	"$cms_partials"
	"$cms_scss"
)
certs_includes=("${lms_includes[@]}")

# Destination directories for generated assets
vendor_js="common/static/common/js/vendor"
vendor_css="common/static/common/css/vendor"
xmodule_fragments="common/static/xmodule"
lms_css="lms/static/css"
cms_css="cms/static/css"
certs_css="lms/static/certificates/css"


#########################################################################
# GLOBAL VARIABLES
# These get modified when we process command-line arguments.
#########################################################################

# What to build
stage=""
env="prod"
systems=("lms" "cms")

# Destination directories for generated assets
static_root="test_root/static"

# Themes: for each (theme_dir, theme_name) pair,
# theme_dir/theme_name is a potential theme path that
# we'll check for.
theme_dirs=()   # Empty is treated as 'none'
theme_names=()  # Empty is treated as 'all in search dirs'

# run: a 'function pointer' to either _echo_and_run_command or _echo_command,
#      both of which are defined below.
#
# All shell commands invoked by this script that mutate the system
# are wrapped in a call to '"$run" ...'. This gives us two benefits:
#  1. Commands are always echoed before they are executed, making it
#     easier for users to understand & debug the script from its output.
#  2. If the user passses --dry-run, we set run="_echo_command",
#     allowing to the script to be run with command printed but not executed.
run="_echo_and_run_command"


#########################################################################
# FUNCTIONS
#########################################################################

# Print script usage information.
show_usage ( ) {
	echo "Usage: $SCRIPT_NAME [<OPTIONS>] [<STAGE>] [<OPTIONS>]"
	echo
	echo "$ABOUT"
	echo
	echo "You can specify one build stage."
	echo "Otherwise, all of them will be run."
    echo
	echo "Stages:"
	echo "    npm                Copy npm-installed assets"
	echo "    xmodule            Copy XModule fragments"
	echo "    webpack            Run Webpack"
	echo "    css                Compile default SCSS"
	echo "    themes             Compile themes' SCSS"
	echo
	echo "Options:"
	echo "    -h|--help                       Display this help message."
	echo "    -d|--dry-run                    Print shell commands but do not run them."
	echo "    -e|--env <ENV>                  Compilation environment (prod or dev)."
	echo "                                    Default: $env"
	echo "    -r|--static-root <STATIC_ROOT>  Path for Webpack output."
	echo "                                    Default: $static_root"
	echo "    --systems <SYSTEM> ...          Specify lms and/or cms."
	echo "                                    Default: ${systems[*]:-(none)}"
	echo "    --theme-dirs <THEME_DIR> ...    Specify one or more theme search dirs."
	echo "                                    Default: ${theme_dirs[*]:-(none)}"
	echo "    --themes <THEME> ...            Themes to compile from theme-dirs."
	echo "                                    Default: ${theme_names[*]:-(all)}"
}

# Print a formatted error message.
show_error ( ) {
	local error_message="$1"

	echo -e "${COL_ERR}${SCRIPT_NAME}: error: ${error_message}${COL_OFF}"
}

# Print a formatted error message, and exit the script unsuccessfully.
fail ( ) {
	local error_message="$1"

	show_error "$error_message"
	exit 1
}

# Print a formatted error message, tell the user how to view the script's usage info,
# and exit the script unsucessfully. Use this function when the error is simply
# that the script has been called wrong.
fail_usage ( ) {
	local error_message="$1"

	show_error "$error_message"
	echo
	echo "Try '$SCRIPT_NAME -h' or '$SCRIPT_NAME --help' for more information."
	exit 1
}

# Log the beginning of a "section" (a larger part of the script).
log_section_start ( ) {
	local section_description="$*"

	echo -e "${COL_LOG}=====================================================================================$COL_OFF"
	echo -e "${COL_LOG} $section_description $COL_OFF"
	echo -e "${COL_LOG}-------------------------------------------------------------------------------$COL_OFF"
}

# Log the end of a "section" (a larger part of the script).
log_section_end ( ) {
	local section_description="$*"

	echo -e "${COL_LOG}-------------------------------------------------------------------------------$COL_OFF"
	echo -e "${COL_LOG} $section_description $COL_OFF"
	echo -e "${COL_LOG}=====================================================================================$COL_OFF"
}

# Log a line of information.
log ( ) {
	local log_line="$*"

	echo -e "${COL_LOG}$SCRIPT_NAME: $log_line $COL_OFF"
}

# Print a shell command (without running it).
# Command should be passed as separate arguments.
_echo_command ( ) {
	local command_components=("$@")

	echo -e "${COL_RUN}${command_components[*]}${COL_OFF}"
}

# Print & execute a shell command.
# Command should be passed as separate arguments.
_echo_and_run_command ( ) {
	local command_components=("$@")

	_echo_command "${command_components[@]}"
	"${command_components[@]}"
}

# Compile a directory of SCSS into CSS, generating RTL CSS as needed.
#
# TODO: Unlike its Python API, libsass-python's CLI (sassc) only supports compiling individual
#       SCSS files, not entire directories.  However, the CLIs for dart-sass and node-sass
#       both *do* support compiling entire directories. So, if/when we upgrade to one of those
#       libraries, much of this function can be replaced with a single CLI call.
#       https://github.com/openedx/edx-platform/issues/31607
compile_scss_dir ( ) {
	local scss_env="$1"         # 1: Environment (dev or prod). For output styling.
	local scss_src_root="$2"    # 2: Path to source directory containing SCSS.
	local css_dest_root="$3"    # 3: Path to target directory for CSS.
	shift 3
	local include_paths=("$@")  # Remaining args: Search paths for SCSS imports.

	local sassc_options=()

	# Add output-style option, depending on environment.
	if [[ "$scss_env" == dev ]] ; then
		sassc_options+=("--output-style=nested")
	else
		sassc_options+=("--output-style=compressed")
	fi

	# For each include path, add it to the list of SCSS compile options.
	for include_path in "${include_paths[@]}" ; do
		sassc_options+=("--include-path=$include_path")
	done

	# For each SCSS file $scss_src within $scss_src_root (recursive),
	# excluding underscore-prefixed (i.e., partial) SCSS files...
	while read -r -d $'\0' scss_src ; do

		# Translate source path into destination path:
		scss_src_relative="${scss_src#"$scss_src_root"}"           # Chop off SCSS root dir prefix.
		css_dest_relative="${scss_src_relative%.scss}.css"         # Replace file extension.
		css_dest="$css_dest_root/$css_dest_relative"               # Prepend CSS root dir.

		css_dest_dir="$(dirname "$css_dest")"                      # Find immediate parent dir of CSS file target...
		"$run" mkdir -p "$css_dest_dir"                            # ...and create it if it doesn't exist.
		"$run" sassc "${sassc_options[@]}" "$scss_src" "$css_dest" # Compile the SCSS.

		# If this is an LTR (left-to-right) SCSS source file...
		if [[ "$scss_src" != *-rtl.scss ]] ; then

			# then determine what the name of the RTL source and target would be...
			rtl="$scss_src_relative"      # (Start with the SCSS-root-relative source path,
			rtl="${rtl%-ltr.scss}"        #  then strip any -ltr.scss suffix,
			rtl="${rtl%.scss}"            #  as well as any strip any .scss suffix.
			rtl="${rtl}-rtl"              #  then finally append -rtl)
			rtl_scss_src="$scss_src_root/$rtl.scss"
			rtl_css_dest="$css_dest_root/$rtl.css"

			# and if the source RTL SCSS doesn't exist...
			if [[ ! -f "$rtl_scss_src" ]] ; then

				# then we know that the target RTL CSS will not be generated via SCSS compilation,
				# so we must auto-generate it here from the LTR CSS.
				"$run" rtlcss "$css_dest" "$rtl_css_dest"
			fi
		fi
	done < <(find "$scss_src_root" -type f -name '*.scss' \! -name '_*' -print0)
}


#########################################################################
# COMMAND-LINE ARGUMENT PROCESSING
#########################################################################

# Stick the DEFAULT_OPTS in front of the actual command-line
# arguments ($@) so that they are processed below as default arguments.
# We split DEFAULT_OPTS on spaces, which shellcheck doesn't like
# (because it won't work on filenames with spaces) but there isn't really
# a better way to do this.
# shellcheck disable=SC2086
set -- $DEFAULT_OPTS "$@"

# Loop through arguments list.
while [[ "$#" -gt 0 ]] ; do
	case "$1" in

		-h|--help)
			show_usage
			exit 0
			;;

		-d|--dry-run)
			run="_echo_command"
			log "DRY RUN: Commands will be printed but not executed!"
			shift
			;;

		-e|--env)
			case "$2" in
				dev|prod)
					env="$2"
					;;
				*)
					fail_usage "expected prod or dev, got: $2"
					;;
			esac
			env="$2"
			shift 2
			;;

		-r|--static-root)
			if [[ "$#" -eq 1 ]] ; then
				fail_usage "Missing value for $1"
			fi
			static_root="$2"
			shift 2
			;;

		--themes)
			shift
			theme_names=()
			# Append args as theme names until we hit an option ( -* ).
			while [[ "$#" -gt 0 ]] && ! [[ "$1" = -* ]]; do
				theme_names+=("$1")
				shift
			done
			;;

		--theme-dirs)
			shift
			theme_dirs=()
			# Append args as theme dirs until we hit an option ( -* ).
			while [[ "$#" -gt 0 ]] && [[ "$1" != -* ]]; do
				theme_dirs+=("$1")
				shift
			done
			;;

		--systems)
			shift
			systems=()
			# Treat args as systems until we hit an option ( -* ).
			while [[ "$#" -gt 0 ]] && ! [[ "$1" = -* ]]; do
				systems+=("$1")
				shift
			done
			;;

		npm|xmodule|webpack|css|themes)
			if [[ -z "$stage" ]] ; then
				stage="$1"
			else
				fail_usage "Cannot specify a second stage: $1"
			fi
			shift
			;;

		-*)
			fail_usage "Unrecognized option: $1"
			;;
		*)
			fail_usage "Unexpected argument: $1"
			;;
	esac
done

# Boolean flags for each system.
# Non-empty string is true; empty string is false.
do_lms=""
do_cms=""
if [[ "${#systems[@]}" -eq 0 ]] ; then
	fail_usage "You must specify one or more system"
fi
for system in "${systems[@]}" ; do
	case "$system" in
		lms)
			do_lms="T"
			;;
		cms)
			do_cms="T"
			;;
		*)
			fail_usage "Valid systems are: lms, cms. Got: $1"
			;;
	esac
done

# Static roots for Webpack output
static_root_lms="$static_root"
static_root_cms="$static_root/studio"

# Build a list of paths to themes to compile.
# For each theme search folder...
theme_paths=()
for theme_dir in "${theme_dirs[@]}" ; do

	# Make sure the search folder exists.
	if [[ ! -d "$theme_dir" ]] ; then
		fail "provided --theme-dir is not a directory: $theme_dir"
	fi

	# For each item in the search folder...
	for theme_dir_item in "$theme_dir"/* ; do

		# Ensure the item is a subfolder.
		if [[ ! -d "$theme_dir_item" ]] ; then
			continue
		fi
		# If it's a subfolder, then we have to assume it's a theme.
		# It might not be a theme, but that's OK. Compiling a folder that's
		# not a theme is basically a no-op.

		# If no theme names were provided, then that means we want every theme
		# in every search dir. So, add this subfolder to our list of themes to
		# compile.
		if [[ "${#theme_names[@]}" = 0 ]] ; then
			theme_paths+=("$theme_dir_item")
			continue
		fi

		# If theme names were provided, then add this subfolder if and only if
		# it matches one of the provided theme names.
		for theme_name in "${theme_names[@]}" ; do
			if [[ "$(basename "$theme_dir_item")" = "$theme_name" ]] ; then
				theme_paths+=("$theme_dir_item")
				break
			fi
		done
	done
done


#########################################################################
# BUILD STAGES
# We do one of these (if $stage is set) or all of them (if unset).
#########################################################################

if [[ -z "$stage" ]] || [[ "$stage" = npm ]] ; then

	log_section_start "Copying npm-installed assets..."

	log "Ensuring vendor directories exist..."
	"$run" mkdir -p "$vendor_js"
	"$run" mkdir -p "$vendor_css"

	log "Copying studio-frontend JS & CSS from node_modules into vendor directores..."
	while read -r -d $'\0' src_file ; do
		if [[ "$src_file" = *.css ]] || [[ "$src_file" = *.css.map ]] ; then
			"$run" cp --force "$src_file" "$vendor_css"
		else
			"$run" cp --force "$src_file" "$vendor_js"
		fi
	done < <(find "$node_modules/@edx/studio-frontend/dist" -type f -print0)

	log "Copying certain JS modules from node_modules into vendor directory..."
	"$run" cp --force \
		"$node_modules/backbone.paginator/lib/backbone.paginator.js" \
		"$node_modules/backbone/backbone.js" \
		"$node_modules/bootstrap/dist/js/bootstrap.bundle.js" \
		"$node_modules/hls.js/dist/hls.js" \
		"$node_modules/jquery-migrate/dist/jquery-migrate.js" \
		"$node_modules/jquery.scrollto/jquery.scrollTo.js" \
		"$node_modules/jquery/dist/jquery.js" \
		"$node_modules/moment-timezone/builds/moment-timezone-with-data.js" \
		"$node_modules/moment/min/moment-with-locales.js" \
		"$node_modules/picturefill/dist/picturefill.js" \
		"$node_modules/requirejs/require.js" \
		"$node_modules/underscore.string/dist/underscore.string.js" \
		"$node_modules/underscore/underscore.js" \
		"$node_modules/which-country/index.js" \
	    "$vendor_js"

	log "Copying certain JS developer modules into vendor directory..."
	if [[ "$env" = dev ]] ; then
		"$run" cp --force "$node_modules/sinon/pkg/sinon.js" "$vendor_js"
		"$run" cp --force "$node_modules/squirejs/src/Squire.js" "$vendor_js"
	else
		# TODO: https://github.com/openedx/edx-platform/issues/31768
		# In the old implementation of this scipt (pavelib/assets.py), these two
		# developer libraries were copied into the JS vendor directory whether not
		# the build was for prod or dev. In order to exactly match the output of
		# the old script, this script will also copy them in for prod builds.
		# However, in the future, it would be good to only copy them for dev
		# builds. Furthermore, these libraries should not be `npm install`ed
		# into prod builds in the first place.
		"$run" cp --force "$node_modules/sinon/pkg/sinon.js" "$vendor_js" || true      # "|| true" means "tolerate errors"; in this case,
		"$run" cp --force "$node_modules/squirejs/src/Squire.js" "$vendor_js" || true  # that's "tolerate if these files don't exist."
	fi

	log_section_end "Done copying npm-installed assets."
fi

if [[ -z "$stage" ]] || [[ "$stage" = xmodule ]] ; then

	log_section_start "Copying XModule fragments..."

	# Note:
    # Copying xmodule_assets is incompatible with setting the django path because
    # of an unfortunate call to settings.configure(), so we must clear
	# DJANGO_SETTINGS_MODULE before calling the script.

	"$run" env \
		"DJANGO_SETTINGS_MODULE=" \
		xmodule_assets "$xmodule_fragments"

	log_section_end "Done copying XModule fragments."
fi

if [[ -z "$stage" ]] || [[ "$stage" = webpack ]] ; then

	log_section_start "Running Webpack..."

	node_env="production"
	if [[ "$env" = dev ]]; then
		node_env="development"
	fi

	"$run" env \
		"NODE_ENV=$node_env" \
		"STATIC_ROOT_LMS=$static_root_lms" \
		"STATIC_ROOT_CMS=$static_root_cms" \
		webpack --progress "--config=webpack.$env.config.js"

	log_section_end "Done running Webpack."
fi

if [[ -z "$stage" ]] || [[ "$stage" = css ]] ; then

	log_section_start "Compiling default SCSS..."

	if [[ -n "$do_lms" ]] ; then
		log "Compiling default LMS SCSS."
		compile_scss_dir "$env" "$lms_scss" "$lms_css" "${lms_includes[@]}"
		log "Compiling default certificates SCSS."
		compile_scss_dir "$env" "$certs_scss" "$certs_css" "${certs_includes[@]}"
	fi
	if [[ -n "$do_cms" ]] ; then
		log "Compiling default CMS SCSS."
		compile_scss_dir "$env" "$cms_scss" "$cms_css" "${cms_includes[@]}"
	fi

	log_section_end "Done compiling default SCSS."
fi

if [[ -z "$stage" ]] || [[ "$stage" = themes ]] ; then

	for theme_path in "${theme_paths[@]}" ; do

		log_section_start "Compiling SCSS for theme at: $theme_path..."

		# Theme SCSS source roots.
		theme_lms_scss="$theme_path/lms/static/sass"
		theme_cms_scss="$theme_path/cms/static/sass"
		theme_certs_scss="$theme_path/lms/static/certificates/sass"

		# Theme SCSS dependency roots (include lists are order-sensitive!)
		theme_cms_partials="$theme_path/cms/static/sass/partials"
		theme_lms_partials="$theme_path/lms/static/sass/partials"
		theme_lms_includes=(
			"${common_includes[@]}"
			"$theme_lms_partials"
			"$lms_partials"
			"$lms_scss"
		)
		theme_cms_includes=(
			"${common_includes[@]}"
			"$lms_partials"
			"$theme_cms_partials"
			"$cms_partials"
			"$cms_scss"
		)
		theme_certs_includes=(
			"${common_includes[@]}"
			"$theme_lms_partials"
			"$theme_lms_scss"
		)

		# Theme CSS target roots.
		theme_lms_css="$theme_path/lms/static/css"
		theme_cms_css="$theme_path/cms/static/css"
		theme_certs_css="$theme_path/lms/static/certificates/css"

		if [[ -n "$do_lms" ]] ; then
			if [[ -d "$theme_lms_scss" ]] ; then
				log "Compiling default LMS SCSS into theme's CSS directory."
				compile_scss_dir "$env" "$lms_scss" "$theme_lms_css" "${theme_lms_includes[@]}"
				log "Compiling theme's LMS SCSS into theme's CSS directory."
				compile_scss_dir "$env" "$theme_lms_scss" "$theme_lms_css" "${theme_lms_includes[@]}"
			else
				log "Theme has no LMS SCSS; skipping."
			fi
			if [[ -d "$theme_certs_scss" ]] ; then
				log "Compiling theme's certificate SCSS into theme's CSS directory."
				compile_scss_dir "$env" "$theme_certs_scss" "$theme_certs_css" "${theme_certs_includes[@]}"
			else
				log "Theme has no certificate SCSS; skipping."
			fi
		fi
		if [[ -n "$do_cms" ]] ; then
			if [[ -d "$theme_cms_scss" ]] ; then
				log "Compiling default CMS SCSS into theme's CSS directory."
				compile_scss_dir "$env" "$cms_scss" "$theme_cms_css" "${theme_cms_includes[@]}"
				log "Compiling theme's CMS SCSS into theme's CSS directory."
				compile_scss_dir "$env" "$theme_cms_scss" "$theme_cms_css" "${theme_cms_includes[@]}"
			else
				log "Theme has no CMS SCSS; skipping."
			fi
		fi

		log_section_end "Done compiling SCSS for theme at: $theme_path"
	done

fi
