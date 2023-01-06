#!/bin/sh
#
# Post-process node_modules.
#
# Run this from the root of edx-platform,
# after node_modules are installed,
# but before trying to compile static assets.
#
# Background:
#
#  Some parts of the edx-platform frontend are built to use assets
#  from node_modules, as you'd expect. Other (older) parts are not.
#  These parts share some dependencies.
#
#  We want package.json to be the canonical source of package versioning.
#  So, we install modules into node_modules, as is typical.
#  Then, we use this script to copy some scripts and styles out of node_modules
#  and into the places where the older frontends need them to be.

USAGE="Usage: $0 [ (-n|--node-modules) NODE_MODULES_PATH ]"

# By default, we look for node_modules in the current directory.
# Some Open edX distributions may want node_modules to be located somewhere
# else, so we let this be configured with -n|--node-modules.
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
		-n|--node-modules)
			shift
			if [ $# -eq 0 ]; then
				echo "Error: Missing value for -n/--node-modules"
				echo "$USAGE"
				exit 1
			fi
			NODE_MODULES_PATH="$1"
			shift
			;;
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
echo "Post-processing npm assets...."
echo "  Working directory == '$(pwd)'"
echo "  NODE_MODULES_PATH == '$NODE_MODULES_PATH'"
echo "  CSS_VENDOR_PATH   == '$CSS_VENDOR_PATH'"
echo "  JS_VENDOR_PATH    == '$JS_VENDOR_PATH'"
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

# Copy certain node_modules libraries into vendor directory.
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

# Copy certain node_modules developer libraries into vendor directory.
# Since they're just developer libraries, they might not exist in a production build pipeline.
# So, let the error pass silently (`... || true`) if the copy fails.
cp --force "$NODE_MODULES_PATH/sinon/pkg/sinon.js" "$JS_VENDOR_PATH" || true
cp --force "$NODE_MODULES_PATH/squirejs/src/Squire.js" "$JS_VENDOR_PATH" || true

# Stop echoing.
set +x

echo "-------------------------------------------------------------------------"
echo "Done post-processing npm assets."
echo "-------------------------------------------------------------------------"
