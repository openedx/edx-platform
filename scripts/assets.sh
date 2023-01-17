#!/usr/bin/env bash
ABOUT="Various assets processing/building/collection utility for Open edX"

set -euo pipefail

THIS_SCRIPT="$0"
SCRIPT_NAME="${SCRIPT_NAME:-$THIS_SCRIPT}"

DEFAULT_STATIC_ROOT="${DEFAULT_STATIC_ROOT:-./test_root/static}"
DEFAULT_THEMES_DIR="${DEFAULT_THEMES_DIR:-}"
DEFAULT_COLLECT_SETTINGS="${DEFAULT_COLLECT_SETTINGS:-lms.envs.production}"

HL="\e[36m"  # Highlight color (currently: cyan)
NC="\e[0m"   # Normal color

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

show_error ( ) {
	echo "$SCRIPT_NAME: error: $1"
}

fail ( ) {
	show_error "$1"
	exit 1
}

fail_usage ( ) {
	show_error "$1"
	echo
	echo "Try '$SCRIPT_NAME -h' or '$SCRIPT_NAME --help' for more information."
	exit 1
}

log_section_start ( ) {
	echo -e "$HL=====================================================================================$NC"
	echo -e "$HL $1 $NC"
	echo -e "$HL-------------------------------------------------------------------------$NC"
}

log_section_end ( ) {
	echo -e "$HL-------------------------------------------------------------------------$NC"
	echo -e "$HL $1 $NC"
	echo -e "$HL=====================================================================================$NC"
}

log_step ( ) {
	echo -e "$HL $SCRIPT_NAME: $@ $NC"
}

compile_scss_dir ( ) {
	# TODO: Document args
	local style="$1"
	local scss_src="$2"
	local css_dest="$3"
	shift 3
	local include_paths=("$@")

	local sassc_options=()
	if [[ "$style" == dev ]] ; then
		sassc_options+=("--output-style=nested")
	else
		sassc_options+=("--output-style=compressed")
	fi
	for include_path in "${include_paths[@]}" ; do
		sassc_options+=("--include-path=$include_path")
	done

	# Navigate into `scss_src` and recursively print out relative paths for all SCSS
	# files, excluding underscore-prefixed ones, using `sed` to chop off the file extension.
	# For each filepath, run `sassc` and, if appropriate, `rtlcss`.
	# TODO: Unlike its Python API, libsass-python's CLI does not support compiling entire
	#       directories, so we must implement that logic ourselves. After we upgrade
	#       to node-sass or dart-sass, though, this logic might be able to be simplified.
	for rel_path in $(cd "$scss_src" && \
		              find . \( -name \*.scss -and \! -name _\* \) | \
					  sed -n 's/.scss$//p')
	do
		# Make sure the destination directory exists.
		mkdir -p "$(dirname "$css_dest/$rel_path")"
		# Compile one SCSsassc_options file into a CSS file.
		sassc \
			"${sassc_options[@]}" \
			"$scss_src/$rel_path.scss" \
			"$css_dest/$rel_path.css"
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
}

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

do_lms="T"
do_cms="T"

# In https://github.com/openedx/wg-developer-experience/issues/150,
# we will allow this to be configured via a new --node-modules option.
node_modules="node_modules"

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
			while [[ "$#" -gt 0 ]] && ! [[ "$1" = -* ]]; do
				theme_names+=("$1")
				shift
			done
			;;
	
		--theme-dirs)
			shift
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
			# Only one subcommand can be supplied.
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
	# These are not configurable yet, but that could be changed if necessary.
	JS_VENDOR_PATH="./common/static/common/js/vendor"
	CSS_VENDOR_PATH="./common/static/common/css/vendor"
	EDX_UI_TOOLKIT_VENDOR_PATH="./common/static/edx-ui-toolkit"

	log_step "Creating vendor directories..."
	mkdir -p "$JS_VENDOR_PATH"
	mkdir -p "$CSS_VENDOR_PATH"
	mkdir -p "$EDX_UI_TOOLKIT_VENDOR_PATH"

	log_step "Copying studio-frontend JS from node_modules into vendor directory..."
	find "$node_modules/@edx/studio-frontend/dist" \
		-type f \! -name \*.css \! -name \*.css.map -print0 | \
		xargs --null cp --target-directory="$JS_VENDOR_PATH"

	log_step "Copying studio-frontend CSS from node_modules into vendor directory..."
	find "$node_modules/@edx/studio-frontend/dist" \
		-type f \( -name \*.css -o -name \*.css.map \) -print0 | \
		xargs --null cp --target-directory="$CSS_VENDOR_PATH"

	log_step "Copying certain JS modules from node_modules into vendor directory..."
	set -x
	cp --force \
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
		"$JS_VENDOR_PATH"
	set +x

	if [[ "$env" = dev ]] ; then
		log_step "Copying certain JS developer modules into vendor directory..."
		cp --force "$node_modules/sinon/pkg/sinon.js" "$JS_VENDOR_PATH"
		cp --force "$node_modules/squirejs/src/Squire.js" "$JS_VENDOR_PATH"
	fi

	log_section_end "Done copying static assets from node_modules."
fi


if [[ "$subcommand" = build ]] || [[ "$subcommand" = xmodule ]] ; then
	
	log_section_start "Processing assets from xmodule..."

    # Collecting xmodule assets is incompatible with setting the django path, because
    # of an unfortunate call to settings.configure()
	DJANGO_SETTINGS_MODULE="" \
		xmodule_assets "common/static/xmodule"

	log_section_end "Done processing assets from xmodule."
fi

if [[ "$subcommand" = build ]] || [[ "$subcommand" = webpack ]] ; then
	
	log_section_start "Running webpack..."

	node_env="production"
	webpack_config_file="webpack.prod.config.js"
	if [[ "$env" = dev ]]; then
		node_env="development"
		webpack_config_file="webpack.dev.config.js"
	fi
	NODE_ENV="$node_env" \
		STATIC_ROOT_LMS="$static_root_lms" \
		STATIC_ROOT_CMS="$static_root_cms" \
		webpack --progress "--config=$webpack_config_file"

	log_section_end "Done running webpack."
fi

common_scss="common/static/sass"
lms_scss="lms/static/sass"
lms_partials="lms/static/sass/partials"
cms_scss="cms/static/sass"
cms_partials="cms/static/sass/partials"
certs_scss="lms/static/certificates/sass"

lms_css="lms/static/css"
cms_css="cms/static/css"
certs_css="lms/static/certificates/css"

common_includes=(
	"common/static"
	"$common_scss"
	"$node_modules"
	"$node_modules/@edx"
)
lms_includes=(
	"${common_includes[@]}"
	"$lms_scss"
	"$lms_partials"
)
cms_includes=(
	"${common_includes[@]}"
	"$cms_scss"
	"$cms_partials"
	"$lms_partials"
)
certs_includes=("${lms_includes[@]}")

if [[ "$subcommand" = build ]] || [[ "$subcommand" = common ]] ; then
	
	log_section_start "Compiling static assets for common theme..."

	log_step "Removing existing generated CSS first."
	rm -rf "$lms_css" "$cms_css" "$certs_css"
	if [[ -n "$do_lms" ]] ; then
		log_step "Compiling default LMS SCSS."
		compile_scss_dir "$env" "$lms_scss" "$lms_css" "${lms_includes[@]}"
		log_step "Compiling default certificates SCSS."
		compile_scss_dir "$env" "$certs_scss" "$certs_css" "${certs_includes[@]}"
	fi
	if [[ -n "$do_cms" ]] ; then 
		log_step "Compiling default CMS SCSS."
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

		theme_lms_scss="$theme_path/lms/static/sass"
		theme_lms_partials="$theme_path/lms/static/sass/partials"
		theme_cms_scss="$theme_path/cms/static/sass"
		theme_cms_partials="$theme_path/cms/static/sass/partials"
		theme_certs_scss="$theme_path/lms/static/certificates/sass"

		theme_lms_css="$theme_path/lms/static/css"
		theme_cms_css="$theme_path/cms/static/css"
		theme_certs_css="$theme_path/lms/static/certificates/css"

		theme_lms_includes=(
			"${common_includes[@]}"
			"$theme_lms_partials"
			"$lms_partials"
			"$lms_scss"
		)
		theme_cms_includes=(
			"${common_includes[@]}"
			"$theme_cms_partials"
			"$cms_partials"
			"$cms_scss"
		)
		theme_certs_includes=(
			"${common_includes[@]}"
			"$theme_lms_partials"
			"$theme_lms_scss"
		)

		log_step "Removing theme's existing generated CSS first."
		rm -rf "$theme_lms_css" "$theme_cms_css" "$theme_certs_css"

		if [[ -n "$do_lms" ]] ; then
			log_step "Compiling default LMS SCSS into theme's CSS directory."
			compile_scss_dir "$env" "$lms_scss" "$theme_lms_css" "${theme_lms_includes[@]}"
			if [[ -d "$theme_lms_scss" ]] ; then
				log_step "Compiling theme's LMS SCSS into theme's CSS directory."
				compile_scss_dir "$env" "$theme_lms_scss" "$theme_lms_css" "${theme_lms_includes[@]}"
			else
				log_step "Theme has no LMS SCSS; skipping."
			fi
			if [[ -d "$theme_certs_scss" ]] ; then
				log_step "Compiling theme's certificate SCSS into theme's CSS directory."
				compile_scss_dir "$env" "$theme_certs_scss" "$theme_certs_css" "${theme_certs_includes[@]}"
			else
				log_step "Theme has no certificate SCSS; skipping."
			fi
		fi
		if [[ -n "$do_cms" ]] ; then 
			log_step "Compiling default CMS SCSS into theme's CSS directory."
			compile_scss_dir "$env" "$cms_scss" "$theme_cms_css" "${theme_cms_includes[@]}"
			if [[ -d "$theme_cms_scss" ]] ; then
				log_step "Compiling theme's CMS SCSS into theme's CSS directory."
				compile_scss_dir "$env" "$theme_cms_scss" "$theme_cms_css" "${theme_cms_includes[@]}"
			else
				log_step "Theme has no CMS SCSS; skipping."
			fi
		fi

		log_section_end "Done compiling them: $theme_path"
	done

fi

if [[ "$subcommand" = collect ]] ; then
	
	log_section_start "Collecting static assets to be served by webserver..."

	if [[ -n "$do_lms" ]] ; then
		./manage.py lms collectstatic --noinput \
			--settings="$collect_django_settings" \
			--ignore "fixtures" \
			--ignore "karma_*.js" \
			--ignore "spec" \
			--ignore "spec_helpers" \
			--ignore "spec-helpers" \
			--ignore "xmodule_js" \
			--ignore "geoip" \
			--ignore "sass"
	fi
	if [[ -n "$do_cms" ]] ; then
		./manage.py cms collectstatic --noinput \
			--settings="$collect_django_settings" \
			--ignore "fixtures" \
			--ignore "karma_*.js" \
			--ignore "spec" \
			--ignore "spec_helpers" \
			--ignore "spec-helpers" \
			--ignore "xmodule_js" \
			--ignore "geoip" \
			--ignore "sass"
	fi

	log_section_end "Done collecting static assets to be served by webserver."
fi

if [[ "$subcommand" = watch-themes ]] ; then

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
