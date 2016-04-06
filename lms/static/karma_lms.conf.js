// LMS JavaScript tests, using RequireJS.
//
// To run all the tests and print results to the console:
//
//   karma start lms/static/karma_lms.conf.js
//
//
// To run the tests for debugging: Debugging can be done in any browser but
// Chrome's developer console debugging experience is best.
//
//   karma start lms/static/karma_lms.conf.js --browsers=BROWSER --single-run=false
//
//
// To run the tests with coverage and junit reports:
//
//   karma start lms/static/karma_lms.conf.js --browsers=BROWSER
//   --coverage --junitreportpath=<xunit_report_path> --coveragereportpath=<report_path>
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
    {pattern: 'xmodule_js/common_static/js/test/i18n.js', included: false},
    {pattern: 'xmodule_js/common_static/coffee/src/ajax_prefix.js', included: false},
    {pattern: 'xmodule_js/common_static/js/src/logger.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/requirejs/require.js', included: false},
    {pattern: 'js/RequireJS-namespace-undefine.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/requirejs/text.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.min.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery-ui.min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.simulate.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.cookie.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.timeago.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/flot/jquery.flot.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/CodeMirror/codemirror.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/URI.min.js', included: false},
    {
        pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload.js',
        included: false
    },
    {
        pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.iframe-transport.js',
        included: false
    },
    {pattern: 'xmodule_js/common_static/js/vendor/url.min.js', included: false},
    {pattern: 'xmodule_js/common_static/coffee/src/jquery.immediateDescendents.js', included: false},
    {pattern: 'xmodule_js/common_static/js/xblock/**/*.js', included: false},
    {pattern: 'xmodule_js/common_static/coffee/src/xblock/**/*.js', included: false},
    {pattern: 'coffee/src/instructor_dashboard/**/*.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/sinon-1.17.0.js', included: false},
    {pattern: 'xmodule_js/src/capa/**/*.js', included: false},
    {pattern: 'xmodule_js/src/video/**/*.js', included: false},
    {pattern: 'xmodule_js/src/xmodule.js', included: false},
    {pattern: 'xmodule_js/common_static/js/src/**/*.js', included: false},
    {pattern: 'xmodule_js/common_static/common/js/vendor/underscore.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/underscore.string.min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/backbone-min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/backbone.paginator.min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/edxnotes/annotator-full.min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/test/i18n.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/date.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/moment.min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/moment-with-locales.min.js', included: false},
    {pattern: 'xmodule_js/common_static/common/js/utils/edx.utils.validate.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.event.drag-2.2.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/slick.core.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/slick.grid.js', included: true},

    // Paths to source JavaScript files
    {pattern: 'js/**/*.js', included: false, nocache: true},
    {pattern: 'coffee/src/**/*.js', included: false, nocache: true},
    {pattern: 'common/js/**/*.js', included: false, nocache: true},
    {pattern: 'edx-pattern-library/js/**/*.js', included: false, nocache: true},
    {pattern: 'edx-ui-toolkit/js/**/*.js', included: false, nocache: true},
    {pattern: 'support/js/**/*.js', included: false, nocache: true},
    {pattern: 'teams/js/**/*.js', included: false, nocache: true},
    {pattern: 'xmodule_js/common_static/coffee/**/*.js', included: false, nocache: true},

    // Paths to Jasmine plugins
    {pattern: 'xmodule_js/common_static/js/libs/jasmine-waituntil.js', included: true},
    {pattern: 'xmodule_js/common_static/js/libs/jasmine-extensions.js', included: true},

    // Paths to spec (test) JavaScript files
    {pattern: 'js/spec/**/*.js', included: false, nocache: true},
    {pattern: 'teams/js/spec/**/*.js', included: false, nocache: true},
    {pattern: 'support/js/spec/**/*.js', included: false, nocache: true},

    // Paths to fixture files
    {pattern: 'js/fixtures/**/*.html', included: false, nocache: true},
    {pattern: 'templates/instructor/instructor_dashboard_2/**/*.*', included: false, nocache: true},
    {pattern: 'templates/dashboard/**/*.*', included: false, nocache: true},
    {pattern: 'templates/edxnotes/**/*.*', included: false, nocache: true},
    {pattern: 'templates/fields/**/*.*', included: false, nocache: true},
    {pattern: 'templates/student_account/**/*.*', included: false, nocache: true},
    {pattern: 'templates/student_profile/**/*.*', included: false, nocache: true},
    {pattern: 'templates/verify_student/**/*.*', included: false, nocache: true},
    {pattern: 'templates/file-upload.underscore', included: false, nocache: true},
    {pattern: 'templates/components/header/**/*.*', included: false, nocache: true},
    {pattern: 'templates/components/tabbed/**/*.*', included: false, nocache: true},
    {pattern: 'templates/components/card/**/*.*', included: false, nocache: true},
    {pattern: 'templates/financial-assistance/**/*.*', included: false, nocache: true},
    {pattern: 'templates/search/**/*.*', included: false, nocache: true},
    {pattern: 'templates/discovery/**/*.*', included: false, nocache: true},
    {pattern: 'common/templates/**/*.*', included: false, nocache: true},
    {pattern: 'teams/templates/**/*.*', included: false, nocache: true},
    {pattern: 'support/templates/**/*.*', included: false, nocache: true},
    {pattern: 'templates/bookmarks/**/*.*', included: false, nocache: true},
    {pattern: 'templates/learner_dashboard/**/*.*', included: false, nocache: true},
    {pattern: 'templates/ccx/**/*.*', included: false, nocache: true},

    // override fixture path and other config.
    {pattern: path.join(configModule.appRoot, 'common/static/common/js/jasmine.common.conf.js'), included: true},
    {pattern: 'js/spec/main.js', included: true}
];

var preprocessors = {
    // do not include tests or libraries
    // (these files will be instrumented by Istanbul)
    'js/**/*.js': ['coverage'],
    'coffee/src/**/*.js': ['coverage'],
    'common/js/**/*.js': ['coverage'],
    'support/js/**/*.js': ['coverage'],
    'teams/js/**/*.js': ['coverage'],
    'xmodule_js/common_static/coffee/**/*.js': ['coverage']
};

module.exports = function (config) {
    var commonConfig = configModule.getConfig(config),
        localConfig = {
            files: files,
            preprocessors: preprocessors
        };

    config.set(_.extend(commonConfig, localConfig));
};

