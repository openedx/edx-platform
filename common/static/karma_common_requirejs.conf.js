// Common JavaScript tests, using RequireJS.
//
//
// To run all the tests and print results to the console:
//
//   karma start common/static/karma_common_requirejs.conf.js
//
//
// To run the tests for debugging: Debugging can be done in any browser but Chrome's developer console debugging experience is best.
//
//   karma start karma_common_requirejs.conf.js --browsers=BROWSER --single-run=false
//
//
// To run the tests with coverage and junit reports:
//
//   karma start karma_common_requirejs.conf.js --browsers=BROWSER --coverage --junitreportpath=<xunit_report_path> --coveragereportpath=<report_path>
//
// where `BROWSER` could be Chrome or Firefox.
//
//

'use strict';
var path = require('path');
var _ = require('underscore');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var files = [
    {pattern: 'js/vendor/jquery.min.js', included: false},
    {pattern: 'js/vendor/jasmine-imagediff.js', included: false},
    {pattern: 'js/libs/jasmine-stealth.js', included: false},
    {pattern: 'js/libs/jasmine-waituntil.js', included: false},
    {pattern: 'js/vendor/jquery.simulate.js', included: false},
    {pattern: 'js/vendor/jquery.truncate.js', included: false},
    {pattern: 'common/js/vendor/underscore.js', included: false},
    {pattern: 'js/vendor/underscore.string.min.js', included: false},
    {pattern: 'js/vendor/backbone-min.js', included: false},
    {pattern: 'js/vendor/backbone.paginator.min.js', included: false},
    {pattern: 'js/vendor/jquery.timeago.js', included: false},
    {pattern: 'js/vendor/URI.min.js', included: false},
    {pattern: 'coffee/src/ajax_prefix.js', included: false},
    {pattern: 'js/test/add_ajax_prefix.js', included: false},
    {pattern: 'js/test/i18n.js', included: false},
    {pattern: 'coffee/src/jquery.immediateDescendents.js', included: false},
    {pattern: 'js/vendor/requirejs/text.js', included: false},
    {pattern: 'js/vendor/sinon-1.17.0.js', included: false},

    // Paths to source JavaScript files
    {pattern: 'common/js/**/*.js', included: false},

    // Paths to spec (test) JavaScript files
    {pattern: 'common/js/spec/**/*.js', included: false},

    // Paths to fixture files
    {pattern: 'common/templates/**/*.*', included: false},

    // override fixture path and other config.
    {pattern: 'test_config.js', included: true},
    'common/js/spec/main_requirejs.js'
];

module.exports = function (config) {
    var commonConfig = configModule.getConfig(config),
        localConfig = {
            files: files
        };

    config.set(_.extend(commonConfig, localConfig));
};