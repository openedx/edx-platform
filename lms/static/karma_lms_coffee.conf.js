// LMS Coffee Script Tests.
//
// To run all the tests and print results to the console:
//
//   karma start lms/static/karma_lms_coffee.conf.js
//
//
// To run the tests for debugging: Debugging can be done in any browser
// but Chrome's developer console debugging experience is best.
//
//   karma start lms/static/karma_lms_coffee.conf.js --browsers=BROWSER --single-run=false
//
//
// To run the tests with coverage and junit reports:
//
//   karma start lms/static/karma_lms_coffee.conf.js --browsers=BROWSER
// --coverage --junitreportpath=<xunit_report_path> --coveragereportpath=<report_path>
//
// where `BROWSER` could be Chrome or Firefox.
//

/* jshint node: true */
/*jshint -W079 */

'use strict';
var path = require('path');
var _ = require('underscore');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var files = [
    // override fixture path and other config.
    {pattern: path.join(configModule.appRoot, 'common/static/common/js/jasmine.common.conf.js'), included: true},

    // vendor files
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.min.js', included: true},
    {pattern: 'xmodule_js/common_static/js/test/i18n.js', included: true},
    {pattern: 'xmodule_js/common_static/coffee/src/ajax_prefix.js', included: true},
    {pattern: 'xmodule_js/common_static/js/src/logger.js', included: true},
    {pattern: 'xmodule_js/common_static/common/js/vendor/underscore.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/jasmine-imagediff.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/requirejs/require.js', included: true},
    {pattern: 'js/RequireJS-namespace-undefine.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery-ui.min.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.cookie.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/flot/jquery.flot.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/moment.min.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/moment-with-locales.min.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/CodeMirror/codemirror.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/URI.min.js', included: true},
    {pattern: 'xmodule_js/common_static/coffee/src/jquery.immediateDescendents.js', included: true},
    {pattern: 'xmodule_js/common_static/js/xblock/*.js', included: true},
    {pattern: 'xmodule_js/common_static/coffee/src/xblock/*.js', included: true},
    {pattern: 'moment_requirejs.js', included: true},
    {pattern: 'xmodule_js/src/capa/*.js', included: true},
    {pattern: 'xmodule_js/src/video/*.js', included: true},
    {pattern: 'xmodule_js/src/xmodule.js', included: true},

    // source files
    {pattern: 'coffee/src/**/*.js', included: true, nocache: true},

    // spec files
    {pattern: 'coffee/spec/**/*.js', included: true, nocache: true},

    // Fixtures
    {pattern: 'coffee/fixtures/**/*.*', included: true, nocache: true}
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