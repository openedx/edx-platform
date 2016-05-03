// Karma config for cms-squire suite.
// Docs in common/static/common/js/karma.common.conf.js

/* jshint node: true */
/*jshint -W079 */
'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var files = {
    libraryFiles: [
    {pattern: 'xmodule_js/common_static/js/vendor/requirejs/require.js', included: false},
    {pattern: 'xmodule_js/common_static/coffee/src/ajax_prefix.js', included: false},
    {pattern: 'xmodule_js/common_static/js/src/utility.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery-ui.min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.cookie.js', included: false},
    {pattern: 'xmodule_js/common_static/common/js/vendor/underscore.js', included: false},
    {pattern: 'xmodule_js/common_static/common/js/vendor/underscore.string.js', included: false},
    {pattern: 'xmodule_js/common_static/common/js/vendor/backbone.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/backbone-associations-min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/backbone.paginator.min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/timepicker/jquery.timepicker.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.leanModal.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.form.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/html5-input-polyfills/number-polyfill.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/sinon-1.17.0.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/Squire.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/jasmine-imagediff.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/CodeMirror/codemirror.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/domReady.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/URI.min.js', included: false},
    {pattern: 'xmodule_js/common_static/js/libs/jasmine-extensions.js', included: true},
    {pattern: 'xmodule_js/src/xmodule.js', included: false},
    {pattern: 'xmodule_js/common_static/coffee/src/jquery.immediateDescendents.js', included: false},
    {pattern: 'xmodule_js/common_static/js/test/i18n.js', included: false},
    {pattern: 'xmodule_js/common_static/js/xblock/**/*.js', included: false},
    {pattern: 'xmodule_js/common_static/coffee/src/xblock/**/*.js', included: false},
    {pattern: 'xmodule_js/common_static/js/vendor/URI.min.js', included: false},
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
    {pattern: 'xmodule_js/common_static/js/vendor/requirejs/text.js', included: false},
    {pattern: 'common/js/utils/require-serial.js', included: true}
    ],

    sourceFiles: [
    {pattern: 'coffee/src/**/*.js', included: false},
    {pattern: 'js/collections/**/*.js', included: false},
    {pattern: 'js/models/**/*.js', included: false},
    {pattern: 'js/utils/**/*.js', included: false},
    {pattern: 'js/views/**/*.js', included: false},
    {pattern: 'common/js/**/*.js', included: false}
    ],

    specFiles: [
    {pattern: 'coffee/spec/**/*.js', included: false},
    {pattern: 'js/spec/**/*.js', included: false}
    ],

    fixtureFiles: [
    {pattern: 'coffee/fixtures/**/*.*', included: false},
    {pattern: 'templates/**/*.*', included: false},
    {pattern: 'common/templates/**/*.*', included: false}
    ],

    runAndConfigFiles: [
    {pattern: path.join(configModule.appRoot, 'common/static/common/js/jasmine.common.conf.js'), included: true},
    'coffee/spec/main_squire.js'
    ]
};

module.exports = function (config) {
    configModule.configure({
        config: config,
        files: files
    });
};
