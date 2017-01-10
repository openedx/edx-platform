define([
    'edx-ui-toolkit/js/utils/string-utils',
    'edx-ui-toolkit/js/utils/html-utils',
    'edx-ui-toolkit/js/utils/date-utils',
    'domReady!',
    'jquery',
    'jquery-migrate',
    'backbone',
    'underscore',
    'gettext'
],
    function(StringUtils, HtmlUtils, DateUtils) {
        'use strict';

        // Install utility classes in the edX namespace to make them
        // available to code that doesn't use RequireJS,
        // e.g. XModules and XBlocks.
        if (window) {
            window.edx = window.edx || {};
            window.edx.StringUtils = StringUtils;
            window.edx.HtmlUtils = HtmlUtils;
            window.edx.DateUtils = DateUtils;
        }
    });
