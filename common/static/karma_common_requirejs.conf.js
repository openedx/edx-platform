// Karma config for common-requirejs suite.
// Docs in common/static/common/js/karma.common.conf.js

/* jshint node: true */
/*jshint -W079 */

'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var files = {
    libraryFilesToInclude: [
        {pattern: 'js/libs/jasmine-extensions.js', included: true}
    ],

    libraryFiles: [
        {pattern: 'coffee/src/**/*.js'},
        {pattern: 'common/js/spec_helpers/**/*.js'},
        {pattern: 'common/js/vendor/**/*.js'},
        {pattern: 'js/libs/**/*.js'},
        {pattern: 'js/test/**/*.js'},
        {pattern: 'js/vendor/**/*.js'}
    ],

    sourceFiles: [
        {pattern: 'common/js/components/**/!(*spec).js'},
        {pattern: 'common/js/utils/**/!(*spec).js'}
    ],

    specFiles: [
        {pattern: 'common/js/spec/**/*spec.js'}
    ],

    fixtureFiles: [
        {pattern: 'common/templates/**/*.*'}
    ],

    runFiles: [
        {pattern: 'common/js/spec/main_requirejs.js', included: true}
    ]
};

var normalizePathsForCoverageFunc = function (appRoot, pattern) {
    return path.join(appRoot, '/common/static/' + pattern);
};

module.exports = function (config) {
    configModule.configure({
        config: config,
        files: files,
        normalizePathsForCoverageFunc: normalizePathsForCoverageFunc
    });
};
