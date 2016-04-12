// Xmodule Tests
//
// To run all the tests and print results to the console:
//
//   karma start common/lib/xmodule/xmodule/js/karma_xmodule.conf.js
//
//
// To run the tests for debugging: Debugging can be done in any browser
// Chrome's developer console debugging experience is the best though
//
//   karma start common/lib/xmodule/xmodule/js/karma-xmodule.conf.js --browsers=BROWSER --single-run=false
//
//
// To run the tests with coverage and junit reports:
//
//   karma start common/lib/xmodule/xmodule/js/karma-xmodule.conf.js
//  --browsers=BROWSER --coverage --junitreportpath=<xunit_report_path> --coveragereportpath=<report_path>
//
// where `BROWSER` could be Chrome or Firefox.
//

/* jshint node: true */
/*jshint -W079 */

'use strict';
var path = require('path');
var _ = require('underscore');
var configModule = require(path.join(__dirname, 'common_static/common/js/karma.common.conf.js'));

var files = [
    // override fixture path and other config.
    {pattern: path.join(configModule.appRoot, 'common/static/common/js/jasmine.common.conf.js'), included: true},

    {pattern: 'common_static/js/vendor/jquery.min.js', included: true},
    {pattern: 'common_static/js/test/i18n.js', included: true},
    {pattern: 'common_static/coffee/src/ajax_prefix.js', included: true},
    {pattern: 'common_static/js/src/logger.js', included: true},
    {pattern: 'common_static/js/vendor/jasmine-imagediff.js', included: true},
    {pattern: 'common_static/js/libs/jasmine-waituntil.js', included: true},
    {pattern: 'common_static/js/libs/jasmine-extensions.js', included: true},
    {pattern: 'common_static/js/vendor/requirejs/require.js', included: true},
    {pattern: 'RequireJS-namespace-undefine.js', included: true},
    {pattern: 'common_static/js/vendor/jquery-ui.min.js', included: true},
    {pattern: 'common_static/js/vendor/jquery.ui.draggable.js', included: true},
    {pattern: 'common_static/js/vendor/jquery.cookie.js', included: true},
    {pattern: 'common_static/js/vendor/json2.js', included: true},
    {pattern: 'common_static/common/js/vendor/underscore.js', included: true},
    {pattern: 'common_static/js/vendor/backbone-min.js', included: true},
    {pattern: 'common_static/js/vendor/jquery.leanModal.js', included: true},
    {pattern: 'common_static/js/vendor/CodeMirror/codemirror.js', included: true},
    {pattern: 'common_static/js/vendor/tinymce/js/tinymce/jquery.tinymce.min.js', included: true},
    {pattern: 'common_static/js/vendor/tinymce/js/tinymce/tinymce.full.min.js', included: true},
    {pattern: 'common_static/js/vendor/jquery.timeago.js', included: true},
    {pattern: 'common_static/js/vendor/sinon-1.17.0.js', included: true},
    {pattern: 'common_static/js/test/add_ajax_prefix.js', included: true},
    {pattern: 'common_static/js/src/utility.js', included: true},
    {pattern: 'public/js/split_test_staff.js', included: true},
    {pattern: 'common_static/js/src/accessibility_tools.js', included: true},
    {pattern: 'common_static/js/vendor/moment.min.js', included: true},
    {pattern: 'spec/main_requirejs.js', included: true},
    {pattern: 'src/word_cloud/d3.min.js', included: true},

    // Paths to source JavaScript files
    {pattern: 'src/xmodule.js', included: true, nocache: true},
    {pattern: 'src/**/*.js', included: true, nocache: true},

    // Paths to spec (test) JavaScript files
    {pattern: 'spec/helper.js', included: true, nocache: true},
    {pattern: 'spec/**/*.js', included: true, nocache: true},

    // Paths to fixture files
    {pattern: 'fixtures/*.*', included: false, served: true, nocache: true},

    {pattern: 'karma_runner.js', included: true}
];

var preprocessors = {
    // do not include tests or libraries
    // (these files will be instrumented by Istanbul)
    'src/**/*.js': ['coverage']
};

module.exports = function (config) {
    var commonConfig = configModule.getConfig(config, false),
        localConfig = {
            files: files,
            preprocessors: preprocessors
        };

    config.set(_.extend(commonConfig, localConfig));
};