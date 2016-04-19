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
var libraryFiles = [
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
    {pattern: 'common/js/vendor/backbone-min.js', included: true},
    {pattern: 'js/vendor/jquery.timeago.js', included: true},
    {pattern: 'js/vendor/URI.min.js', included: true},
    {pattern: 'coffee/src/ajax_prefix.js', included: true},
    {pattern: 'js/test/add_ajax_prefix.js', included: true},
    {pattern: 'js/test/i18n.js', included: true},
    {pattern: 'coffee/src/jquery.immediateDescendents.js', included: true},
    {pattern: 'js/vendor/jquery.leanModal.js', included: true},
    {pattern: 'js/vendor/draggabilly.js', included: true},
    {pattern: 'edx-ui-toolkit/js/utils/global-loader.js', included: true},
    {pattern: 'edx-pattern-library/js/modernizr-custom.js', included: true},
    {pattern: 'edx-pattern-library/js/afontgarde.js', included: true},
    {pattern: 'edx-pattern-library/js/edx-icons.js', included: true}
];

// Paths to source JavaScript files
var sourceFiles = [
    {pattern: 'js/xblock/**/*.js', included: true},
    {pattern: 'coffee/src/**/*.js', included: true},
    {pattern: 'js/src/**/*.js', included: true},
    {pattern: 'js/capa/src/**/*.js', included: true}
];

// Paths to spec (test) JavaScript files
var specFiles = [
    {pattern: 'coffee/spec/**/*.js', included: true},
    {pattern: 'js/spec/**/*.js', included: true},
    {pattern: 'js/capa/spec/**/*.js', included: true}
];

// Paths to fixture files
var fixtureFiles = [
    {pattern: 'js/fixtures/**/*.html', included: false},
    {pattern: 'js/capa/fixtures/**/*.html', included: false},
    {pattern: 'common/templates/**/*.underscore', included: false}
];

// do not include tests or libraries
// (these files will be instrumented by Istanbul)
var preprocessors = (function () {
    var preprocessFiles = {};

    _.flatten([sourceFiles, specFiles]).forEach(function (file) {
        var pattern = _.isObject(file) ? file.pattern : file;
        pattern = path.join(configModule.appRoot, '/common/static/' + pattern);
        preprocessFiles[pattern] = ['coverage'];
    });

    return preprocessFiles;
}());

module.exports = function (config) {
    var commonConfig = configModule.getConfig(config, false),
        files = _.flatten([libraryFiles, sourceFiles, specFiles, fixtureFiles]),
        localConfig;

    // add nocache in files if coverage is not set
    if (!config.coverage) {
        files.forEach(function (f) {
            if (_.isObject(f)) {
                f.nocache = true;
            }
        });
    }

    localConfig = {
        files: files,
        preprocessors: preprocessors
    };

    config.set(_.extend(commonConfig, localConfig));
};
