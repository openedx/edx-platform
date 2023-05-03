// Karma config for common-requirejs suite.
// Docs and troubleshooting tips in common/static/common/js/karma.common.conf.js

/* eslint-env node */

'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var options = {

    includeCommonFiles: true,

    normalizePathsForCoverageFunc: function(appRoot, pattern) {
        return path.join(appRoot, '/common/static/' + pattern);
    },

    libraryFiles: [
        {pattern: 'js/libs/**/*.js'},
        {pattern: 'js/test/**/*.js'},
        {pattern: 'js/vendor/**/*.js'}
    ],

    // Make sure the patterns in sourceFiles and specFiles do not match the same file.
    // Otherwise Istanbul which is used for coverage tracking will cause tests to not run.
    sourceFiles: [],

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

module.exports = function(config) {
    configModule.configure(config, options);
};
