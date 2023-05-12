/* eslint-env node */

// Karma config for xmodule suite.
// Docs and troubleshooting tips in common/static/common/js/karma.common.conf.js

'use strict';

// eslint-disable-next-line no-var
var path = require('path');

// eslint-disable-next-line no-var
var configModule = require(path.join(__dirname, 'common_static/common/js/karma.common.conf.js'));

// eslint-disable-next-line no-var
var options = {

    useRequireJs: false,

    normalizePathsForCoverageFunc: function(appRoot, pattern) {
        return pattern;
    },

    libraryFilesToInclude: [],
    libraryFiles: [],
    sourceFiles: [],
    specFiles: [],

    fixtureFiles: [
        {pattern: 'fixtures/*.*'},
        {pattern: 'fixtures/hls/**/*.*'}
    ],

    runFiles: [
        {pattern: 'karma_runner_webpack.js', webpack: true}
    ],

    preprocessors: {}
};

options.runFiles
    .filter(function(file) { return file.webpack; })
    .forEach(function(file) {
        options.preprocessors[file.pattern] = ['webpack'];
    });

module.exports = function(config) {
    configModule.configure(config, options);
};
