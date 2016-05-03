// Karma config for cms-squire suite.
// Docs in common/static/common/js/karma.common.conf.js

/* jshint node: true */
/*jshint -W079 */
'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var files = {
    libraryFilesToInclude: [
        {pattern: 'xmodule_js/common_static/js/libs/jasmine-extensions.js', included: true}
    ],

    libraryFiles: [
        {pattern: 'edx-pattern-library/js/**/*.js'},
        {pattern: 'edx-ui-toolkit/js/**/*.js'},
        {pattern: 'xmodule_js/common_static/coffee/src/**/*.js'},
        {pattern: 'xmodule_js/common_static/common/js/vendor/**/*.js'},
        {pattern: 'xmodule_js/common_static/js/**/*.js'},
        {pattern: 'xmodule_js/src/**/*.js'},
    ],

    sourceFiles: [
        {pattern: 'coffee/src/**/!(*spec).js'},
        {pattern: 'common/js/**/!(*spec).js'},
        {pattern: 'js/**/!(*spec).js'}
    ],

    specFiles: [
        {pattern: 'coffee/spec/**/*spec.js'},
        {pattern: 'js/spec/**/*spec.js'}
    ],

    fixtureFiles: [
        {pattern: 'coffee/fixtures/**/*.*'},
        {pattern: 'common/templates/**/*.*'},
        {pattern: 'templates/**/*.*'}
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
