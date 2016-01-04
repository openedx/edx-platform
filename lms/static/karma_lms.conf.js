// Karma config for lms suite.
// Docs and troubleshooting tips in common/static/common/js/karma.common.conf.js

/* eslint-env node */
'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var options = {

    includeCommonFiles: true,

    // Avoid adding files to this list. Use RequireJS.
    libraryFilesToInclude: [
        {pattern: '../../common/static/common/js/vendor/jquery.js', included: true},
        {pattern: '../../common/static/common/js/vendor/jquery-migrate.js', included: true},
        {pattern: '../../common/static/js/vendor/jquery.event.drag-2.2.js', included: true},
        {pattern: '../../common/static/js/vendor/slick.core.js', included: true},
        {pattern: '../../common/static/js/vendor/slick.grid.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/timepicker/jquery.timepicker.js', included: false}
    ],

    libraryFiles: [
        {pattern: 'js/RequireJS-namespace-undefine.js'}
    ],

    // Make sure the patterns in sourceFiles and specFiles do not match the same file.
    // Otherwise Istanbul which is used for coverage tracking will cause tests to not run.
    sourceFiles: [
        {pattern: 'coffee/src/**/!(*spec).js'},
        {pattern: 'discussion/js/**/!(*spec).js'},
        {pattern: 'js/**/!(*spec|djangojs).js'},
        {pattern: 'lms/js/**/!(*spec).js'},
        {pattern: 'support/js/**/!(*spec).js'},
        {pattern: 'teams/js/**/!(*spec).js'}
    ],

    specFiles: [
        {pattern: '../**/*spec.js'}
    ],

    fixtureFiles: [
        {pattern: '../**/fixtures/**/*.html'},
        {pattern: '../**/templates/**/*.html'},
        {pattern: '../**/*.underscore'}
    ],

    runFiles: [
        {pattern: 'lms/js/spec/main.js', included: true}
    ]
};

module.exports = function(config) {
    configModule.configure(config, options);
};
