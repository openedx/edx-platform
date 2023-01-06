#!/bin/sh
#
# Copy certain node_modules to other places in edx-platform.
#
# Run this from the root of edx-platform, after node_modules are installed,
# but before trying to compile static assets.
#
# Background:
#
#  Earlier in edx-platform's development, JS and CSS dependencies were
#  committed directly (a.k.a. "vendored in") to the platform.
#  Later on, as NPM became popular, new edx-platform frontends began
#  using package.json to specify dependencies, and of course those new
#  dependencies were installed into node_modules.
#
#  Unfortunately, not all old pages were updated to use package.json.
#  However, rather then continuing to vendor-in the dependencies for
#  the old pages, it was decided to copy the required files from
#  node_modules to the old "vendor" directories. That way, the old
#  pages' dependencies would remain synced with the newer pages'
#  dependencies. That is what this script does.
#
#  This was formerly implemented in pavelib/assets.py. As we are moving
#  away from paver, it was reimplemented in this shell script.
#
#  NOTE: This uses plain POSIX `sh` instead of `bash` for the purpose of
#  maximum portability.

USAGE="Usage: $0"

NODE_MODULES_PATH="./node_modules"

# Vendor destination paths for assets.
# These are not configurable yet, but that could be changed if necessary.
JS_VENDOR_PATH="./common/static/common/js/vendor"
CSS_VENDOR_PATH="./common/static/common/css/vendor"

# Enable stricter sh behavior.
set -eu  

# Parse options.
while [ $# -gt 0 ]; do
	case $1 in
		--help)
			echo "$USAGE"
			exit 0
			;;
		*)
			echo "Error: Unrecognized option: $1"
			echo "$USAGE"
			exit 1
			;;
	esac
done

echo "-------------------------------------------------------------------------"
echo "Copying shared node_modules to 'vendor' directories..."
echo "  Working directory          == '$(pwd)'"
echo "  NODE_MODULES_PATH          == '$NODE_MODULES_PATH'"
echo "  CSS_VENDOR_PATH            == '$CSS_VENDOR_PATH'"
echo "  JS_VENDOR_PATH             == '$JS_VENDOR_PATH'"
echo "-------------------------------------------------------------------------"

# Input validation
if ! [ -d "$NODE_MODULES_PATH" ]; then
	echo "Error: not a directory: $NODE_MODULES_PATH"
	exit 1
fi
if ! [ -d ./common ]; then
	echo "Error: not a directory: ./common"
	echo "Hint: $0 must be run from the root of the edx-platform directory!"
	exit 1
fi

# Echo lines back to user.
set -x

# Create vendor directories.
mkdir -p common/static/common/js/vendor
mkdir -p common/static/common/css/vendor

# Copy studio-frontend assets into into vendor directory.
find "$NODE_MODULES_PATH/@edx/studio-frontend/dist" \
	-type f \! -name \*.css \! -name \*.css.map -print0 | \
	xargs --null cp --target-directory="$JS_VENDOR_PATH"
find "$NODE_MODULES_PATH/@edx/studio-frontend/dist" \
	-type f \( -name \*.css -o -name \*.css.map \) -print0 | \
	xargs --null cp --target-directory="$CSS_VENDOR_PATH"

# Copy certain node_modules scripts into "vendor" directory.
cp --force \
	"$NODE_MODULES_PATH/backbone.paginator/lib/backbone.paginator.js" \
	"$NODE_MODULES_PATH/backbone/backbone.js" \
	"$NODE_MODULES_PATH/bootstrap/dist/js/bootstrap.bundle.js" \
	"$NODE_MODULES_PATH/hls.js/dist/hls.js" \
	"$NODE_MODULES_PATH/jquery-migrate/dist/jquery-migrate.js" \
	"$NODE_MODULES_PATH/jquery.scrollto/jquery.scrollTo.js" \
	"$NODE_MODULES_PATH/jquery/dist/jquery.js" \
	"$NODE_MODULES_PATH/moment-timezone/builds/moment-timezone-with-data.js" \
	"$NODE_MODULES_PATH/moment/min/moment-with-locales.js" \
	"$NODE_MODULES_PATH/picturefill/dist/picturefill.js" \
	"$NODE_MODULES_PATH/requirejs/require.js" \
	"$NODE_MODULES_PATH/underscore.string/dist/underscore.string.js" \
	"$NODE_MODULES_PATH/underscore/underscore.js" \
	"$NODE_MODULES_PATH/which-country/index.js" \
	"$JS_VENDOR_PATH"

# Copy certain node_modules developer scripts into "vendor" directory.
# Since they're just developer libraries, they might not exist in a production build pipeline.
# So, let the error pass silently (`... || true`) if the copy fails.
cp --force "$NODE_MODULES_PATH/sinon/pkg/sinon.js" "$JS_VENDOR_PATH" || true
cp --force "$NODE_MODULES_PATH/squirejs/src/Squire.js" "$JS_VENDOR_PATH" || true

# Stop echoing.
set +x

echo "-------------------------------------------------------------------------"
echo "Done copying shared node_modules."
echo "-------------------------------------------------------------------------"
