#! /bin/sh

# Remove all of the old xmodule coffee and sass directories
# in preparation to switching to use the xmodule_assets script

rm -rf cms/static/coffee/descriptor
rm -rf cms/static/coffee/module
rm -rf cms/static/sass/descriptor
rm -rf cms/static/sass/module
rm -rf lms/static/coffee/module
rm -rf lms/static/sass/module
