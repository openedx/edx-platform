#!/usr/bin/env bash
set -e

###############################################################################
#
#   safelint_thresholds.sh
#
#   The thresholds used for paver run_safelint when used with various CI
#   systems.
#
###############################################################################

# Violations thresholds for failing the build
export SAFELINT_THRESHOLDS='
    {
        "rules": {
            "javascript-concat-html": 313,
            "javascript-escape": 7,
            "javascript-interpolate": 71,
            "javascript-jquery-append": 120,
            "javascript-jquery-html": 313,
            "javascript-jquery-insert-into-target": 26,
            "javascript-jquery-insertion": 30,
            "javascript-jquery-prepend": 12,
            "mako-html-entities": 0,
            "mako-invalid-html-filter": 33,
            "mako-invalid-js-filter": 249,
            "mako-js-html-string": 0,
            "mako-js-missing-quotes": 0,
            "mako-missing-default": 248,
            "mako-multiple-page-tags": 0,
            "mako-unknown-context": 0,
            "mako-unparseable-expression": 0,
            "mako-unwanted-html-filter": 0,
            "python-close-before-format": 0,
            "python-concat-html": 28,
            "python-custom-escape": 13,
            "python-deprecated-display-name": 53,
            "python-interpolate-html": 68,
            "python-parse-error": 0,
            "python-requires-html-or-text": 0,
            "python-wrap-html": 289,
            "underscore-not-escaped": 709
        },
        "total": 2565
    }'
export SAFELINT_THRESHOLDS=${SAFELINT_THRESHOLDS//[[:space:]]/}
