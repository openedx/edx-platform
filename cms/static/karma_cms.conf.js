// Common JavaScript tests, using RequireJS.
//
// To run all the tests and print results to the console:
//
//   karma start cms/static/karma_cms.conf.js
//
//
// To run the tests for debugging: Debugging can be done in any browser
// but Chrome's developer console debugging experience is best.
//
//   karma start cms/static/karma_cms.conf.js --browsers=BROWSER --single-run=false
//
//
// To run the tests with coverage and junit reports:
//
//   karma start cms/static/karma_cms.conf.js --browsers=BROWSER --coverage
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

var libraryFiles = [
    {pattern: 'xmodule_js/common_static/coffee/src/ajax_prefix.js', included: false},
    {pattern: 'xmodule_js/common_static/js/src/utility.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery-ui.min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.cookie.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.simulate.js', included: false},
    {pattern: 'xmodule_js/common_static/common/js/vendor/underscore.js', included: false},
    {pattern: 'xmodule_js/common_static/common/js/vendor/underscore.string.js', included: false},
    {pattern: 'xmodule_js/common_static/common/js/vendor/backbone-min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/backbone-associations-min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/backbone.paginator.min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/backbone-relational.min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/timepicker/jquery.timepicker.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.leanModal.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.ajaxQueue.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.form.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/html5-input-polyfills/number-polyfill.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/sinon-1.17.0.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/Squire.js', included: false},
    {pattern: 'xmodule_js/common_static/js/libs/jasmine-stealth.js', included: false},
    {pattern: 'xmodule_js/common_static/js/libs/jasmine-waituntil.js', included: false},
    {pattern: 'xmodule_js/common_static/js/libs/jasmine-extensions.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/jasmine-imagediff.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/CodeMirror/codemirror.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/**/*.js', included: false},
    {pattern: 'xmodule_js/src/xmodule.js', included: false},
    {pattern: 'xmodule_js/common_static/js/test/i18n.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/draggabilly.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/date.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/domReady.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/URI.min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.smooth-scroll.min.js', included: false},
    {pattern: 'xmodule_js/common_static/coffee/src/jquery.immediateDescendents.js', included: false},
    {pattern: 'xmodule_js/common_static/js/xblock/**/*.js', included: false},
    {pattern: 'xmodule_js/common_static/coffee/src/xblock/**/*.js', included: false},
    {
        pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.iframe-transport.js',
        included: false
    },
    {pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload.js', included: false},
    {
        pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload-process.js',
        included: false
    },
    {
        pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload-validate.js',
        included: false
    },
    {pattern: 'xmodule_js/common_static/js/vendor/mock-ajax.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/requirejs/text.js', included: false},
    {pattern: 'edx-ui-toolkit/js/utils/global-loader.js', included: false},
    {pattern: 'edx-pattern-library/js/modernizr-custom.js', included: false},
    {pattern: 'edx-pattern-library/js/afontgarde.js', included: false},
    {pattern: 'edx-pattern-library/js/edx-icons.js', included: false},
    {pattern: 'edx-pattern-library/js/**/*.js', included: false},
    {pattern: 'edx-ui-toolkit/js/**/*.js', included: false}
];

// Paths to source JavaScript files
var sourceFiles = [
    {pattern: 'coffee/src/**/!(*spec).js', included: false},
    {pattern: 'js/**/!(*spec).js', included: false},
    {pattern: 'common/js/**/!(*spec).js', included: false}
];

// Paths to spec (test) JavaScript files
var specFiles = [
    {pattern: 'coffee/spec/**/*spec.js', included: false},
    {pattern: 'js/spec/**/*spec.js', included: false},
    {pattern: 'js/certificates/spec/**/*spec.js', included: false}
];

// Paths to fixture files
var fixtureFiles = [
    {pattern: 'coffee/fixtures/**/*.underscore', included: false},
    {pattern: 'templates/**/*.underscore', included: false},
    {pattern: 'common/templates/**/*.underscore', included: false}
];

// override fixture path and other config.
var runAndConfigFiles = [
    {pattern: path.join(configModule.appRoot, 'common/static/common/js/jasmine.common.conf.js'), included: true},
    'coffee/spec/main.js'
];

// do not include tests or libraries
// (these files will be instrumented by Istanbul)
var preprocessors = configModule.getPreprocessorObject(_.flatten([sourceFiles, specFiles]));

module.exports = function (config) {
    var commonConfig = configModule.getConfig(config),
        files = _.flatten([libraryFiles, sourceFiles, specFiles, fixtureFiles, runAndConfigFiles]),
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

