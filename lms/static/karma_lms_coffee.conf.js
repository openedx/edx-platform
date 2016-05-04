// Karma config for lms-coffee suite.
// Docs in common/static/common/js/karma.common.conf.js

/* jshint node: true */
/*jshint -W079 */

'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var files = {
    libraryFilesToInclude: [
        {pattern: 'xmodule_js/common_static/js/vendor/requirejs/require.js', included: true},
        {pattern: 'js/spec/main_requirejs_coffee.js', included: true},

        {pattern: 'js/RequireJS-namespace-undefine.js', included: true},
        {pattern: 'xmodule_js/common_static/coffee/src/ajax_prefix.js', included: true},
        {pattern: 'xmodule_js/common_static/common/js/vendor/underscore.js', included: true},
        {pattern: 'xmodule_js/common_static/edx-ui-toolkit/js/utils/global-loader.js', included: true},
        {pattern: 'xmodule_js/common_static/js/src/logger.js', included: true},
        {pattern: 'xmodule_js/common_static/js/test/i18n.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/CodeMirror/codemirror.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery.min.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery.cookie.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/flot/jquery.flot.js', included: true},
        {pattern: 'xmodule_js/common_static/coffee/src/jquery.immediateDescendents.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery-ui.min.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/moment.min.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/moment-with-locales.min.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/URI.min.js', included: true},

        {pattern: 'xmodule_js/common_static/js/xblock/*.js', included: true},
        {pattern: 'xmodule_js/common_static/coffee/src/xblock/*.js', included: true},
        {pattern: 'xmodule_js/src/capa/*.js', included: true},
        {pattern: 'xmodule_js/src/video/*.js', included: true},
        {pattern: 'xmodule_js/src/xmodule.js', included: true},

        {pattern: 'xmodule_js/common_static/js/vendor/jasmine-imagediff.js', included: true},
        {pattern: 'common/js/spec_helpers/jasmine-extensions.js', included: true}
    ],

    libraryFiles: [
        {pattern: 'edx-pattern-library/js/**/*.js'},
        {pattern: 'edx-ui-toolkit/js/**/*.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/**/*.js'}
    ],

    sourceFiles: [
        {pattern: 'coffee/src/**/*.js', included: true},
    ],

    specFiles: [
        {pattern: 'coffee/spec/**/*.js', included: true}
    ],

    fixtureFiles: [
        {pattern: 'coffee/fixtures/**/*.*', included: true}
    ]
};

module.exports = function (config) {
    configModule.configure({
        config: config,
        files: files,
        useRequireJs: false
    });
};
