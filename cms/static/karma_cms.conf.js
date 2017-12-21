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
        {pattern: 'common/static/common/js/vendor/jquery.js', included: true},
        {pattern: 'common/static/common/js/vendor/jquery-migrate.js', included: true}
    ],

    // Make sure the patterns in sourceFiles and specFiles do not match the same file.
    // Otherwise Istanbul which is used for coverage tracking will cause tests to not run.
    sourceFiles: [
        {pattern: 'cms/static/cms/**/!(*spec|djangojs).js'},
        // ormsbee: I think we just got rid of this altogether?
        {pattern: 'cms/static/coffee/src/**/!(*spec).js'},

        {pattern: 'cms/static/js/**/!(*spec|djangojs).js'}
    ],

    specFiles: [
        {pattern: 'cms/static/cms/**/*spec.js'},
        {pattern: 'cms/static/coffee/spec/**/*spec.js'},
        {pattern: 'cms/static/js/certificates/spec/**/*spec.js'},
        {pattern: 'cms/static/js/spec/**/*spec.js'}
    ],

    fixtureFiles: [
        {pattern: 'cms/static/coffee/fixtures/**/*.underscore'},
        {pattern: 'cms/static/templates/**/*.underscore'}
    ],

    runFiles: [
        {pattern: 'cms/static/cms/js/spec/main.js', included: true}
    ]
};

module.exports = function(config) {
    configModule.configure(config, options);
};
