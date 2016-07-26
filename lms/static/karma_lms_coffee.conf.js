// Karma config for lms-coffee suite.
// Docs and troubleshooting tips in common/static/common/js/karma.common.conf.js

/* eslint-env node */
'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var options = {

    useRequireJs: false,
    includeCommonFiles: true,

    // Avoid adding files to this list. Use RequireJS.
    libraryFilesToInclude: [
        {pattern: 'xmodule_js/common_static/js/vendor/requirejs/require.js', included: true},
        {pattern: 'js/RequireJS-namespace-undefine.js', included: true},

        {pattern: 'common/js/vendor/jquery.js', included: true},
        {pattern: 'common/js/vendor/jquery-migrate.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery.event.drag-2.2.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/slick.core.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/slick.grid.js', included: true},

        {pattern: 'xmodule_js/common_static/js/vendor/requirejs/require.js', included: true},

        {pattern: 'xmodule_js/common_static/coffee/src/ajax_prefix.js', included: true},
        {pattern: 'common/js/vendor/jquery.js', included: true},
        {pattern: 'common/js/vendor/jquery-migrate.js', included: true},
        {pattern: 'common/js/vendor/underscore.js', included: true},
        {pattern: 'common/js/xblock/*.js', included: true},
        {pattern: 'xmodule_js/common_static/js/src/logger.js', included: true},
        {pattern: 'xmodule_js/common_static/js/test/i18n.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/CodeMirror/codemirror.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery.cookie.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/flot/jquery.flot.js', included: true},
        {pattern: 'xmodule_js/common_static/coffee/src/jquery.immediateDescendents.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery-ui.min.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/URI.min.js', included: true},

        {pattern: 'xmodule_js/src/capa/*.js', included: true},
        {pattern: 'xmodule_js/src/video/*.js', included: true},
        {pattern: 'xmodule_js/src/xmodule.js', included: true},

        {pattern: 'xmodule_js/common_static/js/vendor/jasmine-imagediff.js', included: true},
        {pattern: 'common/js/spec_helpers/jasmine-extensions.js', included: true},

        {pattern: 'lms/js/spec/main_requirejs_coffee.js', included: true}
    ],

    libraryFiles: [
        {pattern: 'xmodule_js/common_static/js/vendor/**/*.js'}
    ],

    // Make sure the patterns in sourceFiles and specFiles do not match the same file.
    // Otherwise Istanbul which is used for coverage tracking will cause tests to not run.
    sourceFiles: [
        {pattern: 'coffee/src/**/*.js', included: true}
    ],

    specFiles: [
        {pattern: 'coffee/spec/**/*.js', included: true}
    ],

    fixtureFiles: [
        {pattern: 'coffee/fixtures/**/*.*', included: true}
    ]
};

module.exports = function (config) {
    configModule.configure(config, options);
};
