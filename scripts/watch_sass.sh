#!/usr/bin/env bash

# Wait for changes to Sass, and recompile.
# Invoke from repo root as `npm run watch-sass`.
# This script tries to recompile the minimal set of Sass for any given change.

# By default, only watches default Sass.
# To watch themes too, provide colon-separated paths in the EDX_PLATFORM_THEME_DIRS environment variable.
# Each path will be treated as a "theme dir", which means that every immediate child directory is watchable as a theme.
# For example:
#
#   EDX_PLATFORM_THEME_DIRS=/openedx/themes:./themes npm run watch-sass
#
# would watch default Sass as well as /openedx/themes/indigo, /openedx/themes/mytheme, ./themes/red-theme, etc.

set -euo pipefail

COL_SECTION="\e[1;36m"  # Section header color (bold cyan)
COL_LOG="\e[36m"        # Log color (cyan)
COL_WARNING="\e[1;33m"  # Warning (bold yellow)
COL_ERROR="\e[1;31m"    # Error (bold red)
COL_CMD="\e[35m"        # Command echoing (magenta)
COL_OFF="\e[0m"         # Normal color

section() {
    # Print a header in bold cyan to indicate sections of output.
    echo -e "${COL_SECTION}$*${COL_OFF}"
}
log() {
    # Info line. Indented by one space so that it appears as nested under section headers.
    echo -e " ${COL_LOG}$*${COL_OFF}"
}
warning() {
    # Bright yellow warning message.
    echo -e "${COL_WARNING}WARNING: $*${COL_OFF}"
}
error() {
    # Bright red error message.
    echo -e "${COL_ERROR}ERROR: $*${COL_OFF}"
}
echo_quoted_cmd() {
    # Echo args, each single-quoted, so that the user could copy-paste and run them as a command.
    # Indented by two spaces so it appears as nested under log lines.
    echo -e "  ${COL_CMD}$(printf "'%s' " "$@")${COL_OFF}"
}

start_sass_watch() {
    # Start a watch for .scss files in a particular dir. Run in the background.
    #   start_sass_watch NAME_FOR_LOGGING WATCH_ROOT_PATH HANDLER_COMMAND
    local name="$1"
    local path="$2"
    local handler="$3"
    log "Starting watcher for $name:"
    # Note: --drop means that we should ignore any change events that happen during recompilation.
    #       This is good because it means that if you edit 3 files, we won't fire off three simultaneous compiles.
    #       It's not perfect, though, because if you change 3 files, only the first one will trigger a recompile,
    #       so depending on the timing, your latest changes may or may not be picked up. We accept this as a reasonable
    #       tradeoff. Some watcher libraries are smarter than watchdog, in that they wait until the filesystem "settles"
    #       before firing off a the recompilation. This sounds nice but did not seem worth the effort for legacy assets.
    local watch_cmd=(watchmedo shell-command -v --patterns '*.scss' --recursive --drop --command "$handler" "$path")
    echo_quoted_cmd "${watch_cmd[@]}"
    "${watch_cmd[@]}" &
}

clean_up() {
    # Kill all background processes we started.
    # Since they're all 'watchmedo' instances, we can just use killall.
    log "Stopping all watchers:"
    local stop_cmd=(killall watchmedo)
    echo_quoted_cmd "${stop_cmd[@]}"
    "${stop_cmd[@]}" || true
    log "Watchers stopped."
}

warning "'npm run watch-sass' in edx-platform is experimental. Use at your own risk."

if [[ ! -d common/static/sass ]] ; then
    error 'This command must be run from the root of edx-platform!'
    exit 1
fi
if ! type watchmedo 1>/dev/null 2>&1 ; then
    error "command not found: watchmedo"
    log "The \`watchdog\` Python package is probably not installed. You can install it with:"
    log "  pip install -r requirements/edx/development.txt"
    exit 1
fi

trap clean_up EXIT

# Start by compiling all watched Sass right away, mirroring the behavior of webpack --watch.
section "COMPILING SASS:"
npm run compile-sass
echo
echo

section "STARTING DEFAULT SASS WATCHERS:"

# Changes to LMS Sass require a full recompilation, since LMS Sass can be used in CMS and in themes.
start_sass_watch "default LMS Sass" \
    lms/static/sass \
    'npm run compile-sass-dev'

# Changes to default cert Sass only require recompilation of default cert Sass, since cert Sass
# cannot be included into LMS, CMS, or themes.
start_sass_watch "default certificate Sass" \
    lms/static/certificates/sass \
    'npm run compile-sass-dev -- --skip-cms --skip-themes'

# Changes to CMS Sass require recompilation of default & themed CMS Sass, but not LMS Sass.
start_sass_watch "default CMS Sass" \
    cms/static/sass \
    'npm run compile-sass-dev -- --skip-lms'

# Sass changes in common, node_modules, and xmodule all require full recompilations.
start_sass_watch "default common Sass" \
    common/static \
    'npm run compile-sass-dev'
start_sass_watch "node_modules Sass" \
    node_modules \
    'npm run compile-sass-dev'
start_sass_watch "builtin XBlock Sass" \
    xmodule/assets \
    'npm run compile-sass-dev'

export IFS=";"
for theme_dir in ${EDX_PLATFORM_THEME_DIRS:-} ; do
    for theme_path in "$theme_dir"/* ; do

        theme_name="${theme_path#"$theme_dir/"}"
        lms_sass="$theme_path/lms/static/sass"
        cert_sass="$theme_path/lms/static/certificates/sass"
        cms_sass="$theme_path/cms/static/sass"

        if [[ -d "$lms_sass" ]] || [[ -d "$cert_sass" ]] || [[ -d "$cms_sass" ]] ; then
            section "STARTING WATCHERS FOR THEME '$theme_name':"
        fi

        # Changes to a theme's LMS Sass require that the full theme is recompiled, since LMS
        # Sass is used in certs and CMS.
        if [[ -d "$lms_sass" ]] ; then
            start_sass_watch "$theme_name LMS Sass" \
                "$lms_sass" \
                "npm run compile-sass-dev -- -T $theme_dir -t $theme_name --skip-default"
        fi

        # Changes to a theme's certs Sass only requires that its certs Sass be recompiled.
        if [[ -d "$cert_sass" ]] ; then
            start_sass_watch "$theme_name certificate Sass" \
                "$cert_sass" \
                "npm run compile-sass-dev -- -T $theme_dir -t $theme_name --skip-default --skip-cms"
        fi

        # Changes to a theme's CMS Sass only requires that its CMS Sass be recompiled.
        if [[ -d "$cms_sass" ]] ; then
            start_sass_watch "$theme_name CMS Sass" \
                "$cms_sass" \
                "npm run compile-sass-dev -- -T $theme_dir -t $theme_name --skip-default --skip-lms"
        fi

    done
done

sleep infinity &
echo
echo "Watching Open edX LMS & CMS Sass for changes."
echo "Use Ctrl+c to exit."
echo
echo
wait $!

