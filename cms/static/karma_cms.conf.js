/* eslint-env node */

// Karma config for cms suite.
// Docs and troubleshooting tips in common/static/common/js/karma.common.conf.js

'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var options = {

    includeCommonFiles: true,

    libraryFiles: [],

    libraryFilesToInclude: [
        {pattern: 'common/js/vendor/jquery.js', included: true},
        {pattern: 'common/js/vendor/jquery-migrate.js', included: true}
    ],

    // Make sure the patterns in sourceFiles and specFiles do not match the same file.
    // Otherwise Istanbul which is used for coverage tracking will cause tests to not run.
    sourceFiles: [
        {pattern: 'cms/**/!(*spec|djangojs).js'},
        {pattern: 'coffee/src/**/!(*spec).js'},
        {pattern: 'js/**/!(*spec|djangojs).js'}
    ],

    specFiles: [
        {pattern: 'cms/**/*spec.js'},
        {pattern: 'coffee/spec/**/*spec.js'},
        {pattern: 'js/certificates/spec/**/*spec.js'},
        {pattern: 'js/spec/**/*spec.js'}
    ],

    fixtureFiles: [
        {pattern: 'coffee/fixtures/**/*.underscore'},
        {pattern: 'templates/**/*.underscore'}
    ],

    runFiles: [
        {pattern: 'cms/js/spec/main.js', included: true}
    ]
};

module.exports = function(config) {
    configModule.configure(config, options);
};
