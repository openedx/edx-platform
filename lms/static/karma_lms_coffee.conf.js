// LMS Coffee Script Tests.
//
//
// To run all the tests and print results to the console:
//
//   karma start lms/static/karma_lms_coffee.conf.js
//
//
// To run the tests for debugging: Debugging can be done in any browser but Chrome's developer console debugging experience is best.
//
//   karma start lms/static/karma_lms_coffee.conf.js --browsers=BROWSER --single-run=false
//
//
// To run the tests with coverage and junit reports:
//
//   karma start lms/static/karma_lms_coffee.conf.js --browsers=BROWSER --coverage --junitreportpath=<xunit_report_path> --coveragereportpath=<report_path>
//
// where `BROWSER` could be Chrome or Firefox.
//
//

'use strict';
var path = require('path');
var _ = require('underscore');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var files = [
    // override fixture path and other config.
    'test_config.js',

    // include vendor js files but don't add a <script> tag for each
    'xmodule_js/common_static/js/vendor/jquery.min.js',
    'xmodule_js/common_static/js/test/i18n.js',
    'xmodule_js/common_static/coffee/src/ajax_prefix.js',
    'xmodule_js/common_static/js/src/logger.js',
    'xmodule_js/common_static/common/js/vendor/underscore.js',
    'xmodule_js/common_static/js/vendor/jasmine-imagediff.js',
    'xmodule_js/common_static/js/vendor/requirejs/require.js',
    'js/RequireJS-namespace-undefine.js',
    'xmodule_js/common_static/js/vendor/jquery-ui.min.js',
    'xmodule_js/common_static/js/vendor/jquery.cookie.js',
    'xmodule_js/common_static/js/vendor/flot/jquery.flot.js',
    'xmodule_js/common_static/js/vendor/moment.min.js',
    'xmodule_js/common_static/js/vendor/moment-with-locales.min.js',
    'xmodule_js/common_static/js/vendor/CodeMirror/codemirror.js',
    'xmodule_js/common_static/js/vendor/URI.min.js',
    'xmodule_js/common_static/coffee/src/jquery.immediateDescendents.js',
    'xmodule_js/common_static/js/xblock/*.js',
    'xmodule_js/common_static/coffee/src/xblock/*.js',
    'moment_requirejs.js',
    'xmodule_js/src/capa/*.js',
    'xmodule_js/src/video/*.js',
    'xmodule_js/src/xmodule.js',

    // source files
    'coffee/src/**/*.js',

    // spec files
    'coffee/spec/**/*.js',

    // Fixtures
    'coffee/fixtures/**/*.*'
];

var preprocessors = {
    // do not include tests or libraries
    // (these files will be instrumented by Istanbul)
    'coffee/src/**/*.js': ['coverage']
};

module.exports = function (config) {
    var commonConfig = configModule.getConfig(config, false),
        localConfig = {
            files: files,
            preprocessors: preprocessors
        };

    config.set(_.extend(commonConfig, localConfig));
};