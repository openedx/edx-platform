// Karma config for lms-coffee suite.
// Docs in common/static/common/js/karma.common.conf.js

/* jshint node: true */
/*jshint -W079 */

'use strict';
var path = require('path');
var _ = require('underscore');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var libraryFiles = [
    // override fixture path and other config.
    {pattern: path.join(configModule.appRoot, 'common/static/common/js/jasmine.common.conf.js'), included: true},

    // vendor files
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.min.js', included: true},
    {pattern: 'xmodule_js/common_static/js/test/i18n.js', included: true},
    {pattern: 'xmodule_js/common_static/coffee/src/ajax_prefix.js', included: true},
    {pattern: 'xmodule_js/common_static/js/src/logger.js', included: true},
    {pattern: 'xmodule_js/common_static/common/js/vendor/underscore.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/jasmine-imagediff.js', included: true},
    {pattern: 'xmodule_js/common_static/js/libs/jasmine-extensions.js', included: true},
    {pattern: 'xmodule_js/common_static/js/vendor/requirejs/require.js', included: true},
    {pattern: 'js/spec/main_requirejs_coffee.js', included: true},
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
    {pattern: 'xmodule_js/common_static/js/vendor/draggabilly.js', included: false},
    {pattern: 'xmodule_js/common_static/edx-ui-toolkit/js/utils/global-loader.js', included: true},
    {pattern: 'xmodule_js/common_static/edx-pattern-library/js/modernizr-custom.js', included: false},
    {pattern: 'xmodule_js/common_static/edx-pattern-library/js/afontgarde.js', included: false},
    {pattern: 'xmodule_js/common_static/edx-pattern-library/js/edx-icons.js', included: false}
];

// source files
var sourceFiles = [
    {pattern: 'coffee/src/**/*.js', included: true}
];

// spec files
var specFiles = [
    {pattern: 'coffee/spec/**/*.js', included: true}
];

// Fixtures
var fixtureFiles = [
    {pattern: 'coffee/fixtures/**/*.*', included: true}
];

// do not include tests or libraries
// (these files will be instrumented by Istanbul)
var preprocessors = configModule.getPreprocessorObject(_.flatten([sourceFiles, specFiles]));

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
