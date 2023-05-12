/* eslint-env node */

// Karma config for cms-squire suite.
// Docs and troubleshooting tips in common/static/common/js/karma.common.conf.js

'use strict';

// eslint-disable-next-line no-var
var path = require('path');

// eslint-disable-next-line no-var
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

// eslint-disable-next-line no-var
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
        {pattern: 'cms/js/**/!(*spec|djangojs).js'},
        {pattern: 'js/**/!(*spec|djangojs).js'}
    ],

    specFiles: [
        {pattern: 'js/spec/**/*spec.js'}
    ],

    fixtureFiles: [
        {pattern: 'templates/**/*.*'}
    ],

    runFiles: [
        {pattern: 'cms/js/spec/main_squire.js', included: true}
    ]
};

module.exports = function(config) {
    configModule.configure(config, options);
};
