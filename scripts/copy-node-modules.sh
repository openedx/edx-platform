#!/usr/bin/env bash
# Copy certain npm-installed assets from node_modules to other folders in
# edx-platform. These assets are used by certain especially-old legacy LMS & CMS
# frontends that are not set up to import from node_modules directly.
# Many of the destination folders are named "vendor", because they originally
# held vendored-in (directly-committed) libraries; once we moved most frontends
# to use NPM, we decided to keep library versions in-sync by copying to the
# former "vendor" directories.

# Enable stricter error handling.
set -euo pipefail

COL_LOG="\e[36m"  # Log/step/section color (cyan)
COL_OFF="\e[0m"   # Normal color

# Keep these as variables in case we ever want to parameterize this script's
# input or output dirs, as proposed in:
# https://github.com/openedx/wg-developer-experience/issues/150
# https://github.com/openedx/wg-developer-experience/issues/151
node_modules="node_modules"
vendor_js="common/static/common/js/vendor"
vendor_css="common/static/common/css/vendor"

# Stylized logging.
log ( ) {
	echo -e "${COL_LOG}$* $COL_OFF"
}

log "====================================================================================="
log "Copying required assets from node_modules..."
log "-------------------------------------------------------------------------------"

# Start echoing all commands back to user for ease of debugging.
set -x

log "Ensuring vendor directories exist..."
mkdir -p "$vendor_js"
mkdir -p "$vendor_css"

log "Copying studio-frontend JS & CSS from node_modules into vendor directores..."
while read -r -d $'\0' src_file ; do
    if [[ "$src_file" = *.css ]] || [[ "$src_file" = *.css.map ]] ; then
        cp --force "$src_file" "$vendor_css"
    else
        cp --force "$src_file" "$vendor_js"
    fi
done < <(find "$node_modules/@edx/studio-frontend/dist" -type f -print0)

log "Copying certain JS modules from node_modules into vendor directory..."
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
    "$vendor_js"

log "Copying certain JS developer modules into vendor directory..."
if [[ "${NODE_ENV:-production}" = development ]] ; then
    cp --force "$node_modules/sinon/pkg/sinon.js" "$vendor_js"
    cp --force "$node_modules/squirejs/src/Squire.js" "$vendor_js"
else
    # TODO: https://github.com/openedx/edx-platform/issues/31768
    # In the old implementation of this scipt (pavelib/assets.py), these two
    # developer libraries were copied into the JS vendor directory whether not
    # the build was for prod or dev. In order to exactly match the output of
    # the old script, this script will also copy them in for prod builds.
    # However, in the future, it would be good to only copy them for dev
    # builds. Furthermore, these libraries should not be `npm install`ed
    # into prod builds in the first place.
    cp --force "$node_modules/sinon/pkg/sinon.js" "$vendor_js" || true      # "|| true" means "tolerate errors"; in this case,
    cp --force "$node_modules/squirejs/src/Squire.js" "$vendor_js" || true  # that's "tolerate if these files don't exist."
fi

# Done echoing.
set +x

log "-------------------------------------------------------------------------------"
log " Done copying required assets from node_modules."
log "====================================================================================="

