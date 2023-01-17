#!/usr/bin/env bash
ABOUT="Various assets processing/building/collection utility for Open edX"

# Enable stricter error handling.
set -euo pipefail

# True script name, so that we can call ourselves from watchers
THIS_SCRIPT="$0"

# Constants, overridable via environment variables
SCRIPT_NAME="${SCRIPT_NAME:-$THIS_SCRIPT}"                                  # Script name for logging & errors
DEFAULT_STATIC_ROOT="${DEFAULT_STATIC_ROOT:-./test_root/static}"            # Fallback STATIC_ROOT (for Django settings)
DEFAULT_THEMES_DIR="${DEFAULT_THEMES_DIR:-}"                                # Fallback directory to look for themes in
DEFAULT_COLLECT_SETTINGS="${DEFAULT_COLLECT_SETTINGS:-lms.envs.production}" # Fallback `./manage.py collectstatic` settings

# Codes for colored terminal output.
COL_LOG="\e[36m"  # Log/step/section color (cyan)
COL_RUN="\e[35m"  # Executed code echo color (purple)
COL_ERR="\e[31m"  # Error color (red)
COL_OFF="\e[0m"   # Normal color

# Print script usage information.
show_usage ( ) {
	echo "Usage: $SCRIPT_NAME [<OPTIONS>] <SUBCOMMAND> [<OPTIONS>]"
	echo
	echo "$ABOUT"
	echo
	echo "Subcommands:"
	echo "    build               Build all assets (npm+xmodule+webpack+common+themes)"
	echo "     npm                Copy static assets from node_modules"
	echo "     xmodule            Process assets from xmodule"
	echo "     webpack            Run webpack"
	echo "     common             Compile static assets for common theme"
	echo "     themes             Compile static assets for custom themes"
	echo "    collect             Collect static assets to be served by webserver"
	echo "    watch-themes        Watch theme assets for changes and recompile on-the-fly"
	echo
	echo "Options:"
	echo "    -h|--help                       Display this help message."
	echo "    -d|--dry-run                    Print shell commands but do not run them."
	echo "    -e|--env <ENV>                  Environment: prod or dev. Default is prod."
	echo "    -r|--static-root <STATIC_ROOT>  Path for Webpack output."
	echo "                                    Default is $DEFAULT_STATIC_ROOT."
	echo "    -s|--settings <SETTINGS>        Dotted path to Django settings module for asset"
	echo "                                    collection. Default is $DEFAULT_COLLECT_SETTINGS"
	echo "    --systems <SYSTEM> ...          Specify one or more systems: lms, cms. Default is both."
	echo "    --theme-dirs <THEME_DIR> ...    Specify one or more theme search dirs."
	echo "                                    Default is ${DEFAULT_THEMES_DIR:-none}."
	echo "    --themes <THEME> ...            Compile one or more themes from theme search dirs."
	echo "                                    Default is all."
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

# run: a 'function pointer' to either _echo_and_run_command or _echo_command.
#
# All shell commands invoked by this script that mutate the environment
# are wrapped in a call to '"$run" ...'. This gives us two benefits:
#  1. Commands are always echoed before they are executed, making it
#     easier for users to understand & debug the script from its output.
#  2. If the user passses --dry-run, we set run="_echo_command",
#     allowing to the script to be run with command printed but not executed.
run="_echo_and_run_command"

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

# Variables, controlled by command-line options.

subcommand=""
env="prod"

static_root_lms="$DEFAULT_STATIC_ROOT"
static_root_cms="$static_root_lms/studio"
collect_django_settings="$DEFAULT_COLLECT_SETTINGS"

theme_names=()
if [[ -n "$DEFAULT_THEMES_DIR" ]] ; then
	theme_dirs=("$DEFAULT_THEMES_DIR")
else
	theme_dirs=()
fi

# In https://github.com/openedx/wg-developer-experience/issues/150,
# we will allow this to be configured via a new --node-modules option.
node_modules="node_modules"

# "Boolean" variables, controlled by command-line options.
# Non-empty string is "True", empty string is "False".
# As a convention, we use the string "T" for "True".

do_lms="T"
do_cms="T"

# Arguments can take a few different forms, for better or for worse:
#    * Positional arguments (not prefixed with '-')
#    * Flag options, both short (-d) or long (--do-stuff)
#    * Grouped short flag options (-dxy)
#    * Single-value options, both short (-k val, -k=val) and long (--key val, --key=val)
#    * Multi-value options, both short (-k val1 val2 val3) and long (--key val1 val2 val3)
# To simplify the next part of the script, we simplify the args:
#    * Expand grouped short flags into individual short values (-abc => -a -b -c)
#    * Remove the equals sign from value options (--key=val => --key val)
simplified_args=()
while [[ "$#" -gt 0 ]] ; do
	case "$1" in
		--*)
			long_option="${1#--}"
			if [[ "$long_option" == *'='* ]] ; then
				# Long option using equals sign.
				# Split it into key and value as two separate args.
				long_option_key="$(echo "$long_option" | cut -d '=' -f 1)"
				if [[ -z "${long_option_key}" ]] ; then
					# If the key is empty, something's wrong ('-=')
					fail_usage "Bad option: $1"
				fi
				long_option_val="$(echo "$long_option" | cut -d '=' -f 2-)"
				simplified_args+=("--$long_option_key" "$long_option_val")
			else
				# Long option with no equals sign. Good as-is.
				simplified_args+=("$1")
			fi
			;;
		-*)
			short_option="${1#-}"
			if [[ "$short_option" == *'='* ]] ; then
				# Short option using equals sign.
				# Split it into key and value as two separate args.
				short_option_key="$(echo "$short_option" | cut -d '=' -f 1)"
				if [[ "${#short_option_key}" != 1 ]] ; then
					# If the key isn't one character, something's wrong ('-key=val')
					fail_usage "Bad option: $1"
				fi
				short_option_val="$(echo "$short_option" | cut -d '=' -f 2-)"
				simplified_args+=("-$short_option_key" "$short_option_val")
			else
				# Short option(s) with no equals sign.
				# Treat each character as its own short option.
				for (( i=0; i<${#short_option}; i++ )); do
					simplified_args+=("-${short_option:i:1}")
				done
			fi
			;;

		*)
			# Positional argument, or value for an option. Good as-is.
			simplified_args+=("$1")
			;;
	esac
	shift
done

# Now that we've simplified the arguments into a consistent format,
# loop through and process them.
set -- "${simplified_args[@]}"
while [[ "$#" -gt 0 ]] ; do
	case "$1" in

		-h|--help)
			show_usage
			exit 0
			;;

		-d|--dry)
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
			static_root_lms="$2"
			static_root_cms="$2/studio"
			shift 2
			;;

		--themes)
			shift
			# Append args as theme dirs until we hit an option ( -* ).
			while [[ "$#" -gt 0 ]] && ! [[ "$1" = -* ]]; do
				theme_names+=("$1")
				shift
			done
			;;

		--theme-dirs)
			shift
			# Append args as theme dirs until we hit an option ( -* ).
			theme_dirs=()
			while [[ "$#" -gt 0 ]] && [[ "$1" != -* ]]; do
				theme_dirs+=("$1")
				shift
			done
			;;

		--systems)
			shift
			do_lms=""
			do_cms=""
			# Treat args as systems until we hit an option ( -* ).
			while [[ "$#" -gt 0 ]] && ! [[ "$1" = -* ]]; do
				case "$1" in
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
				shift
			done
			if [[ -z "$do_lms" ]] && [[ -z "$do_cms" ]] ; then
				fail_usage "You must specify one or more system"
			fi
			;;

		-s|--settings)
			collect_django_settings="$2"
			shift 2
			;;

		build|npm|xmodule|webpack|common|themes|collect|watch-themes)
			if [[ -z "$subcommand" ]] ; then
				subcommand="$1"
			else
				fail_usage "Cannot specify a second subcommand: $1"
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

if [[ -z "$subcommand" ]] ; then
	fail_usage "Please specify a subcommand"
fi

if [[ "$subcommand" = build ]] || [[ "$subcommand" = npm ]] ; then

	log_section_start "Copying static assets from node_modules..."

	# Vendor destination paths for assets.
	# These are not configurable yet, but that will change as part of
	# https://github.com/openedx/wg-developer-experience/issues/151
	js_vendor_path="common/static/common/js/vendor"
	css_vendor_path="common/static/common/css/vendor"
	edx_ui_toolkit_vendor_path="common/static/edx-ui-toolkit"

	log "Ensuring vendor directories exist..."
	"$run" mkdir -p "$js_vendor_path"
	"$run" mkdir -p "$css_vendor_path"
	"$run" mkdir -p "$edx_ui_toolkit_vendor_path"

	log "Copying studio-frontend JS & CSS from node_modules into vendor directores..."
	find "$node_modules/@edx/studio-frontend/dist" -type f -print0 | \
	while read -r -d $'\0' src_file ; do
		if [[ "$src_file" = *.css ]] || [[ "$src_file" = *.css.map ]] ; then
			"$run" cp --force "$src_file" "$css_vendor_path"
		else
			"$run" cp --force "$src_file" "$js_vendor_path"
		fi
	done

	log "Copying certain JS modules from node_modules into vendor directory..."
	js_vendor_modules=(
		"$node_modules/backbone.paginator/lib/backbone.paginator.js"
		"$node_modules/backbone/backbone.js"
		"$node_modules/bootstrap/dist/js/bootstrap.bundle.js"
		"$node_modules/hls.js/dist/hls.js"
		"$node_modules/jquery-migrate/dist/jquery-migrate.js"
		"$node_modules/jquery.scrollto/jquery.scrollTo.js"
		"$node_modules/jquery/dist/jquery.js"
		"$node_modules/moment-timezone/builds/moment-timezone-with-data.js"
		"$node_modules/moment/min/moment-with-locales.js"
		"$node_modules/picturefill/dist/picturefill.js"
		"$node_modules/requirejs/require.js"
		"$node_modules/underscore.string/dist/underscore.string.js"
		"$node_modules/underscore/underscore.js"
		"$node_modules/which-country/index.js"
	)
	for js_vendor_module in "${js_vendor_modules[@]}" ; do
		"$run" cp --force "$js_vendor_module" "$js_vendor_path"
	done

	log "Copying certain JS developer modules into vendor directory..."
	if [[ "$env" = dev ]] ; then
		"$run" cp --force "$node_modules/sinon/pkg/sinon.js" "$js_vendor_path"
		"$run" cp --force "$node_modules/squirejs/src/Squire.js" "$js_vendor_path"
	else
		# TODO: https://github.com/openedx/edx-platform/issues/31768
		# In the old implementation of this scipt (pavelib/assets.py), these two
		# developer libraries were copied into the JS vendor directory whether not
		# the build was for prod or dev. In order to exactly match the output of
		# the old script, this script will also copy them in for prod builds.
		# However, in the future, it would be good to only copy them for dev
		# builds. Furthermore, these libraries should not be `npm install`ed
		# into prod builds in the first place.
		"$run" cp --force "$node_modules/sinon/pkg/sinon.js" "$js_vendor_path" || true      # "|| true" means "tolerate errors"; in this case,
		"$run" cp --force "$node_modules/squirejs/src/Squire.js" "$js_vendor_path" || true  # that's "tolerate if these files don't exist."
	fi

	log_section_end "Done copying static assets from node_modules."
fi

if [[ "$subcommand" = build ]] || [[ "$subcommand" = xmodule ]] ; then

	log_section_start "Processing assets from xmodule..."

	# Note:
    # Collecting xmodule_assets is incompatible with setting the django path because
    # of an unfortunate call to settings.configure(), so we must clear
	# DJANGO_SETTINGS_MODULE before calling the script.

	"$run" env \
		"DJANGO_SETTINGS_MODULE=" \
		xmodule_assets common/static/xmodule

	log_section_end "Done processing assets from xmodule."
fi

if [[ "$subcommand" = build ]] || [[ "$subcommand" = webpack ]] ; then

	log_section_start "Running webpack..."

	node_env="production"
	if [[ "$env" = dev ]]; then
		node_env="development"
	fi

	"$run" env \
		"NODE_ENV=$node_env" \
		"STATIC_ROOT_LMS=$static_root_lms" \
		"STATIC_ROOT_CMS=$static_root_cms" \
		webpack --progress "--config=webpack.$env.config.js"

	log_section_end "Done running webpack."
fi

# SCSS source roots.
lms_scss="lms/static/sass"
cms_scss="cms/static/sass"
certs_scss="lms/static/certificates/sass"

# SCSS dependency roots (include lists are order-sensitive!)
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

# CSS target roots.
lms_css="lms/static/css"
cms_css="cms/static/css"
certs_css="lms/static/certificates/css"


if [[ "$subcommand" = build ]] || [[ "$subcommand" = common ]] ; then

	log_section_start "Compiling static assets for common theme..."

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

	log_section_end "Done compiling static assets for common theme."
fi

theme_paths=()
for theme_dir in "${theme_dirs[@]}" ; do
	for theme_dir_item in "$theme_dir"/* ; do
		if [[ ! -d "$theme_dir_item" ]] ; then
			continue
		fi
		if [[ "${#theme_names[@]}" = 0 ]] ; then
			theme_paths+=("$theme_dir_item")
			continue
		fi
		for theme_name in "${theme_names[@]}" ; do
			if [[ "$(basename "$theme_dir_item")" = "$theme_name" ]] ; then
				theme_paths+=("$theme_dir_item")
				break
			fi
		done
	done
done

if [[ "$subcommand" = build ]] || [[ "$subcommand" = themes ]] ; then

	for theme_path in "${theme_paths[@]}" ; do

		log_section_start "Compiling static assets for custom theme: $theme_path..."

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

		log_section_end "Done compiling theme: $theme_path"
	done

fi

if [[ "$subcommand" = collect ]] ; then

	log_section_start "Collecting static assets to be served by webserver..."

	if [[ -n "$do_lms" ]] ; then
		"$run" ./manage.py lms collectstatic --noinput \
			--settings "$collect_django_settings" \
			--ignore 'fixtures' \
			--ignore 'karma_*.js' \
			--ignore 'spec' \
			--ignore 'spec_helpers' \
			--ignore 'spec-helpers' \
			--ignore 'xmodule_js' \
			--ignore 'geoip' \
			--ignore 'sass'
	fi
	if [[ -n "$do_cms" ]] ; then
		"$run" ./manage.py cms collectstatic --noinput \
			--settings "$collect_django_settings" \
			--ignore 'fixtures' \
			--ignore 'karma_*.js' \
			--ignore 'spec' \
			--ignore 'spec_helpers' \
			--ignore 'spec-helpers' \
			--ignore 'xmodule_js' \
			--ignore 'geoip' \
			--ignore 'sass'
	fi

	log_section_end "Done collecting static assets to be served by webserver."
fi

if [[ "$subcommand" = watch-themes ]] ; then

	# TODO: implement watchers, both for themes and for other assets
	fail "Watchers do not work yet."

	log_section_start "Starting watchers for theme assets..."
	cleanup="echo 'Cleaning up watchers...'"

	for theme_path in "${theme_paths[@]}" ; do
		theme_dir="$(dirname "$theme_path")"
		theme_name="$(basename "$theme_path")"
		for system in lms cms ; do
			watch_path="$theme_path/$system"
			watchman "--logfile=$(realpath ..)/watchman.log" watch "$watch_path"
			watchman -- trigger "$watch_path" "recompile-scss-on-change--$watch_path" '*scss' -- \
				"$THIS_SCRIPT" themes \
					--theme-dirs "$theme_dir" \
					--themes "$theme_name" \
					--systems "$system"
			cleanup="$cleanup ; watchman watch-del '$watch_path'"
		done
	done

	cleanup="$cleanup ; watchman shutdown-server ; echo 'Done cleaning up watchers.'"
	# Shellcheck will warn us that "$cleanup" will be evaulated now, not
	# when the signal is trapped. In fact, that's exactly what we want.
	# shellcheck disable=SC2064
	trap "$cleanup" EXIT INT HUP TERM

	log_section_end "Watchers started. Use Ctrl-c to exit."
	while true ; do
		sleep 1
	done
fi
