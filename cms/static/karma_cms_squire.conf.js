// Karma config for cms-squire suite.
// Docs in common/static/common/js/karma.common.conf.js

/* jshint node: true */
/*jshint -W079 */
'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var files = {
    libraryFiles: [
        {pattern: 'xmodule_js/common_static/js/vendor/requirejs/require.js'},
        {pattern: 'xmodule_js/common_static/coffee/src/ajax_prefix.js'},
        {pattern: 'xmodule_js/common_static/js/src/utility.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery.min.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery-ui.min.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery.cookie.js'},
        {pattern: 'xmodule_js/common_static/common/js/vendor/underscore.js'},
        {pattern: 'xmodule_js/common_static/common/js/vendor/underscore.string.js'},
        {pattern: 'xmodule_js/common_static/common/js/vendor/backbone.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/backbone-associations-min.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/backbone.paginator.min.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/timepicker/jquery.timepicker.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery.leanModal.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery.form.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/html5-input-polyfills/number-polyfill.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/sinon-1.17.0.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/Squire.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jasmine-imagediff.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/CodeMirror/codemirror.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/domReady.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/URI.min.js'},
        {pattern: 'xmodule_js/common_static/js/libs/jasmine-extensions.js', included: true},
        {pattern: 'xmodule_js/src/xmodule.js'},
        {pattern: 'xmodule_js/common_static/coffee/src/jquery.immediateDescendents.js'},
        {pattern: 'xmodule_js/common_static/js/test/i18n.js'},
        {pattern: 'xmodule_js/common_static/js/xblock/**/*.js'},
        {pattern: 'xmodule_js/common_static/coffee/src/xblock/**/*.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/URI.min.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.iframe-transport.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload-process.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload-validate.js'},
        {pattern: 'xmodule_js/common_static/js/vendor/requirejs/text.js'},
        {pattern: 'common/js/utils/require-serial.js', included: true}
    ],

    sourceFiles: [
        {pattern: 'coffee/src/**/*.js'},
        {pattern: 'js/collections/**/*.js'},
        {pattern: 'js/models/**/*.js'},
        {pattern: 'js/utils/**/*.js'},
        {pattern: 'js/views/**/*.js'},
        {pattern: 'common/js/**/*.js'}
    ],

    specFiles: [
        {pattern: 'coffee/spec/**/*.js'},
        {pattern: 'js/spec/**/*.js'}
    ],

    fixtureFiles: [
        {pattern: 'coffee/fixtures/**/*.*'},
        {pattern: 'templates/**/*.*'},
        {pattern: 'common/templates/**/*.*'}
    ],

    runFiles: [
        {pattern: 'coffee/spec/main_squire.js', included: true}
    ]
};

module.exports = function (config) {
    configModule.configure({
        config: config,
        files: files
    });
};
