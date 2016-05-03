// Karma config for common suite.
// Docs in common/static/common/js/karma.common.conf.js

/* jshint node: true */
/*jshint -W079 */
'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var files = {
    libraryFilesToInclude: [
        {pattern: 'coffee/src/ajax_prefix.js', included: true},
        {pattern: 'js/vendor/draggabilly.js', included: true},
        {pattern: 'js/vendor/jquery.min.js', included: true},
        {pattern: 'coffee/src/jquery.immediateDescendents.js', included: true},
        {pattern: 'js/vendor/jquery.leanModal.js', included: true},
        {pattern: 'js/vendor/jquery.timeago.js', included: true},
        {pattern: 'js/vendor/jquery.truncate.js', included: true},
        {pattern: 'js/vendor/mustache.js', included: true},
        {pattern: 'js/vendor/URI.min.js', included: true},
        {pattern: 'js/test/add_ajax_prefix.js', included: true},
        {pattern: 'js/test/i18n.js', included: true},

        {pattern: 'common/js/vendor/underscore.js', included: true},
        {pattern: 'common/js/vendor/underscore.string.js', included: true},
        {pattern: 'common/js/vendor/backbone.js', included: true},

        {pattern: 'edx-ui-toolkit/js/utils/global-loader.js', included: true},
        {pattern: 'edx-pattern-library/js/modernizr-custom.js', included: true},
        {pattern: 'edx-pattern-library/js/afontgarde.js', included: true},
        {pattern: 'edx-pattern-library/js/edx-icons.js', included: true},

        {pattern: 'js/vendor/jasmine-imagediff.js', included: true},
        {pattern: 'js/libs/jasmine-waituntil.js', included: true},
        {pattern: 'js/libs/jasmine-extensions.js', included: true}
    ],

    libraryFiles: [
    ],

    sourceFiles: [
        {pattern: 'js/xblock/**/*.js', included: true},
        {pattern: 'coffee/src/**/*.js', included: true},
        {pattern: 'js/src/**/*.js', included: true},
        {pattern: 'js/capa/src/**/*.js', included: true}
    ],

    specFiles: [
        {pattern: 'coffee/spec/**/*.js', included: true},
        {pattern: 'js/spec/**/*.js', included: true},
        {pattern: 'js/capa/spec/**/*.js', included: true}
    ],

    fixtureFiles: [
        {pattern: 'js/fixtures/**/*.html'},
        {pattern: 'js/capa/fixtures/**/*.html'},
        {pattern: 'common/templates/**/*.underscore'}
    ]
};

var normalizePathsForCoverageFunc = function (appRoot, pattern) {
    return path.join(appRoot, '/common/static/' + pattern);
};

module.exports = function (config) {
    configModule.configure({
        config: config,
        files: files,
        normalizePathsForCoverageFunc: normalizePathsForCoverageFunc,
        useRequireJs: false
    });
};
