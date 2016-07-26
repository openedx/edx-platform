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
        {pattern: 'common/js/vendor/jquery.js', included: true},
        {pattern: 'common/js/vendor/jquery-migrate.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/jquery.event.drag-2.2.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/slick.core.js', included: true},
        {pattern: 'xmodule_js/common_static/js/vendor/slick.grid.js', included: true}
    ],

    libraryFiles: [
        {pattern: 'js/RequireJS-namespace-undefine.js'}
    ],

    // Make sure the patterns in sourceFiles and specFiles do not match the same file.
    // Otherwise Istanbul which is used for coverage tracking will cause tests to not run.
    sourceFiles: [
        {pattern: 'coffee/src/**/!(*spec).js'},
        {pattern: 'js/**/!(*spec|djangojs).js'},
        {pattern: 'lms/js/**/!(*spec).js'},
        {pattern: 'support/js/**/!(*spec).js'},
        {pattern: 'teams/js/**/!(*spec).js'}
    ],

    specFiles: [
        {pattern: 'js/spec/**/*spec.js'},
        {pattern: 'lms/js/spec/**/*spec.js'},
        {pattern: 'support/js/spec/**/*spec.js'},
        {pattern: 'teams/js/spec/**/*spec.js'},
        {pattern: 'xmodule_js/common_static/coffee/spec/**/*.js'}
    ],

    fixtureFiles: [
        {pattern: 'js/fixtures/**/*.html'},
        {pattern: 'lms/fixtures/**/*.html'},
        {pattern: 'support/templates/**/*.*'},
        {pattern: 'teams/templates/**/*.*'},
        {pattern: 'templates/**/*.*'}
    ],

    runFiles: [
        {pattern: 'lms/js/spec/main.js', included: true}
    ]
};

module.exports = function (config) {
    configModule.configure(config, options);
};
