// Common JavaScript tests
//
// To run all the tests and print results to the console:
//
//   karma start common/static/karma_common.conf.js
//
//
// To run the tests for debugging: Debugging can be done in any browser
// but Chrome's developer console debugging experience is best.
//
//   karma start common/static/karma_common.conf.js --browsers=BROWSER --single-run=false
//
//
// To run the tests with coverage and junit reports:
//
//   karma start common/static/karma_common.conf.js --browsers=BROWSER --coverage
// --junitreportpath=<xunit_report_path> --coveragereportpath=<report_path>
//
// where `BROWSER` could be Chrome or Firefox.
//

/* jshint node: true */
/*jshint -W079 */
'use strict';
var path = require('path');
var _ = require('underscore');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

// Files to load by Karma
var files = [
    // override fixture path and other config.
    {pattern: path.join(configModule.appRoot, 'common/static/common/js/jasmine.common.conf.js'), included: true},

    {pattern: 'js/vendor/jquery.min.js', included: true},
    {pattern: 'js/vendor/jasmine-imagediff.js', included: true},
    {pattern: 'js/libs/jasmine-waituntil.js', included: true},
    {pattern: 'js/libs/jasmine-extensions.js', included: true},
    {pattern: 'js/vendor/jquery.truncate.js', included: true},
    {pattern: 'js/vendor/mustache.js', included: true},
    {pattern: 'common/js/vendor/underscore.js', included: true},
    {pattern: 'js/vendor/underscore.string.min.js', included: true},
    {pattern: 'js/vendor/backbone-min.js', included: true},
    {pattern: 'js/vendor/jquery.timeago.js', included: true},
    {pattern: 'js/vendor/URI.min.js', included: true},
    {pattern: 'coffee/src/ajax_prefix.js', included: true},
    {pattern: 'js/test/add_ajax_prefix.js', included: true},
    {pattern: 'js/test/i18n.js', included: true},
    {pattern: 'coffee/src/jquery.immediateDescendents.js', included: true},
    {pattern: 'js/vendor/jquery.leanModal.js', included: true},

    // Paths to source JavaScript files
    {pattern: 'js/xblock/**/*.js', included: true, nocache: true},
    {pattern: 'coffee/src/**/*.js', included: true, nocache: true},
    {pattern: 'js/src/**/*.js', included: true, nocache: true},
    {pattern: 'js/capa/src/**/*.js', included: true, nocache: true},

    // Paths to spec (test) JavaScript files
    {pattern: 'coffee/spec/**/*.js', included: true, nocache: true},
    {pattern: 'js/spec/**/*.js', included: true, nocache: true},
    {pattern: 'js/capa/spec/**/*.js', included: true, nocache: true},

    // Paths to fixture files
    {pattern: 'js/fixtures/**/*.html', included: false, nocache: true},
    {pattern: 'js/capa/fixtures/**/*.html', included: false, nocache: true},
    {pattern: 'common/templates/**/*.underscore', included: false, nocache: true}
];

var preprocessors = {
    // do not include tests or libraries
    // (these files will be instrumented by Istanbul)
    'js/xblock/**/*.js': ['coverage'],
    'coffee/src/**/*.js': ['coverage'],
    'js/src/**/*.js': ['coverage'],
    'js/capa/src/**/*.js': ['coverage']
};

module.exports = function (config) {
    var commonConfig = configModule.getConfig(config, false),
        localConfig = {
            files: files,
            preprocessors: preprocessors
        };

    config.set(_.extend(commonConfig, localConfig));
};