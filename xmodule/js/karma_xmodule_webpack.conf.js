/* eslint-env node */

// Karma config for xmodule suite.
// Docs and troubleshooting tips in common/static/common/js/karma.common.conf.js

'use strict';

var path = require('path');

var configModule = require(path.join(__dirname, 'common_static/common/js/karma.common.conf.js'));

var options = {

    useRequireJs: false,

    normalizePathsForCoverageFunc: function(appRoot, pattern) {
        return pattern;
    },

    libraryFilesToInclude: [],
    libraryFiles: [],
    sourceFiles: [],
    specFiles: [],

    // fixtureFiles: [
    //     {pattern: 'fixtures/*.*'},
    //     {pattern: 'fixtures/hls/**/*.*'}
    // ],

    fixtureFiles: [
    {
        pattern: path.join(__dirname, 'fixtures/*.*'),
        included: false,
        served: true,
        watched: true
    },
    {
        pattern: path.join(__dirname, 'fixtures/hls/**/*.*'),
        included: false,
        served: true,
        watched: true
    }
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
