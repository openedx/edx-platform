#!/usr/bin/env bash

# Usage:
#   In a CMS or LMS container,
#   from the directory /edx/app/edxapp/edx-platform, run:
#     ./scripts/update-assets-dev.sh
#
# This file is an experimental re-implementation of the asset complation process
# defined by the pavelib.assets:update_assets task in
# https://github.com/openedx/edx-platform/blob/master/pavelib/assets.py.
# As the script name implies, it is only suited to compile assets for usage
# in a development environment, NOT for production. 
#
# It was written as part of the effort to move our dev tools off of Ansible and
# Paver, described here: https://github.com/openedx/devstack/pull/866
# TODO: If the effort described above is abandoned, then this script should
# probably be deleted.

set -xeuo pipefail

# Compile assets for baked-in XBlocks that still use the old
# XModule asset pipeline.
# (reimplementing pavelib.assets:process_xmodule_assets)
# `xmodule_assets` complains if  `DJANGO_SETTINGS_MODULE` is already set,
# so we set it to empty just for this one invocation.
DJANGO_SETTINGS_MODULE='' xmodule_assets common/static/xmodule

# Create JS and CSS vendor directories.
# (reimplementing pavelib.assets:process_npm_assets)
mkdir -p common/static/common/js/vendor
mkdir -p common/static/common/css/vendor

# Copy studio-frontend CSS and JS into vendor directory.
# (reimplementing pavelib.assets:process_npm_assets)
find node_modules/@edx/studio-frontend/dist -type f \( -name \*.css -o -name \*.css.map \) | \
	xargs cp --target-directory=common/static/common/css/vendor
find node_modules/@edx/studio-frontend/dist -type f \! -name \*.css \! -name \*.css.map | \
	xargs cp --target-directory=common/static/common/js/vendor

# Copy certain NPM JS into vedor directory.
# (reimplementing pavelib.assets:process_npm_assets)
cp -f --target-directory=common/static/common/js/vendor \
	node_modules/backbone.paginator/lib/backbone.paginator.js \
	node_modules/backbone/backbone.js \
	node_modules/bootstrap/dist/js/bootstrap.bundle.js \
	node_modules/hls.js/dist/hls.js \
	node_modules/jquery-migrate/dist/jquery-migrate.js \
	node_modules/jquery.scrollto/jquery.scrollTo.js \
	node_modules/jquery/dist/jquery.js \
	node_modules/moment-timezone/builds/moment-timezone-with-data.js \
	node_modules/moment/min/moment-with-locales.js \
	node_modules/picturefill/dist/picturefill.js \
	node_modules/requirejs/require.js \
	node_modules/underscore.string/dist/underscore.string.js \
	node_modules/underscore/underscore.js \
	node_modules/which-country/index.js \
	node_modules/sinon/pkg/sinon.js \
	node_modules/squirejs/src/Squire.js

# Run webpack.
# (reimplementing pavelib.assets:webpack)
NODE_ENV=development \
	STATIC_ROOT_LMS=/edx/var/edxapp/staticfiles \
	STATIC_ROOT_CMS=/edx/var/edxapp/staticfiles/studio \
	JS_ENV_EXTRA_CONFIG="{}" \
	$(npm bin)/webpack --config=webpack.dev.config.js

# Compile SASS for LMS and CMS.
# (reimplementing pavelib.assets:execute_compile_sass)
./manage.py lms compile_sass lms
./manage.py cms compile_sass cms

# Collect static assets for LMS and CMS.
# (reimplementing pavelib.assets:collect_assets)
./manage.py lms collectstatic --noinput \
	--ignore "fixtures"  \
	--ignore "karma_*.js" \
	--ignore "spec" \
	--ignore "spec_helpers" \
	--ignore "spec-helpers" \
	--ignore "xmodule_js" \
	--ignore "geoip" \
	--ignore "sass"
./manage.py cms collectstatic --noinput \
	--ignore "fixtures"  \
	--ignore "karma_*.js" \
	--ignore "spec" \
	--ignore "spec_helpers" \
	--ignore "spec-helpers" \
	--ignore "xmodule_js" \
	--ignore "geoip" \
	--ignore "sass"
