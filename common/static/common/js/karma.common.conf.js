// Common configuration for Karma
/* jshint node: true */
'use strict';

var path = require('path');
var appRoot = path.join(__dirname, '../../../../');

/**
 * Customize the name attribute in xml testcase element
 * @param {Object} browser
 * @param {Object} result
 * @return {String}
 */
function junitNameFormatter(browser, result) {
    return result.suite[0] + ': ' + result.description;
}


/**
 * Customize the classname attribute in xml testcase element
 * @param {Object} browser
 * @return {String}
 */
function junitClassNameFormatter(browser) {
    return "Javascript." + browser.name.split(" ")[0];
}


/**
 * Return array containing default and user supplied reporters
 * @param {Object} config
 * @return {Array}
 */
function reporters(config) {
    var defaultReporters = ['dots', 'junit', 'kjhtml'];
    if (config.coverage) {
        defaultReporters.push('coverage');
    }
    return defaultReporters;
}


/**
 * Split a filepath into basepath and filename
 * @param {String} filepath
 * @return {Object}
 */
function getBasepathAndFilename(filepath) {
    if (!filepath) {
        // these will configure the reporters to create report files relative to this karma config file
        return {
            dir: undefined,
            file: undefined
        };
    }

    var file = filepath.replace(/^.*[\\\/]/, ''),
        dir = filepath.replace(file, '');

    return {
        dir: dir,
        file: file
    };
}


/**
 * Return coverage reporter settings
 * @param {String} config
 * @return {Object}
 */
function coverageSettings(config) {
    var path = getBasepathAndFilename(config.coveragereportpath);
    return {
        dir: path.dir,
        subdir: '.',
        reporters: [
            {type: 'cobertura', file: path.file},
            {type: 'text-summary'}
        ]
    };
}


/**
 * Return junit reporter settings
 * @param {String} config
 * @return {Object}
 */
function junitSettings(config) {
    var path = getBasepathAndFilename(config.junitreportpath);
    return {
        outputDir: path.dir,
        outputFile: path.file,
        suite: 'javascript',
        useBrowserName: false,
        nameFormatter: junitNameFormatter,
        classNameFormatter: junitClassNameFormatter
    };
}

var getConfig = function (config, useRequireJs) {
    useRequireJs = useRequireJs === undefined ? true : useRequireJs;

    var getFrameworkFiles = function () {
        var files = [
            'node_modules/jquery/dist/jquery.js',
            'node_modules/jasmine-core/lib/jasmine-core/jasmine.js',
            'node_modules/karma-jasmine/lib/boot.js',
            'node_modules/karma-jasmine/lib/adapter.js',
            'node_modules/jasmine-jquery/lib/jasmine-jquery.js'
        ];

        if (useRequireJs) {
            files = files.concat([
                'node_modules/requirejs/require.js',
                'node_modules/karma-requirejs/lib/adapter.js'
            ]);
        }

        return files;
    };

    var initFrameworks = function (files) {
        getFrameworkFiles().reverse().forEach(function (f) {
            files.unshift({
                pattern: path.join(appRoot, f),
                included: true,
                served: true,
                watch: false
            });
        });
    };

    initFrameworks.$inject = ['config.files'];

    var customPlugin = {
        'framework:custom': ['factory', initFrameworks]
    };

    return {
        // base path that will be used to resolve all patterns (eg. files, exclude)
        basePath: '',

        // frameworks to use
        // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
        frameworks: ['custom'],

        plugins: [
            'karma-jasmine',
            'karma-jasmine-html-reporter',
            'karma-requirejs',
            'karma-junit-reporter',
            'karma-coverage',
            'karma-chrome-launcher',
            'karma-firefox-launcher',
            customPlugin
        ],


        // list of files to exclude
        exclude: [],

        // karma-reporter
        reporters: reporters(config),


        coverageReporter: coverageSettings(config),


        junitReporter: junitSettings(config),


        // web server port
        port: 9876,


        // enable / disable colors in the output (reporters and logs)
        colors: true,


        // level of logging
        /* possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN
         || config.LOG_INFO || config.LOG_DEBUG */
        logLevel: config.LOG_DEBUG,


        // enable / disable watching file and executing tests whenever any file changes
        autoWatch: false,


        // start these browsers
        // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
        browsers: ['Firefox'],


        // Continuous Integration mode
        // if true, Karma captures browsers, runs the tests and exits
        singleRun: config.singleRun,

        // Concurrency level
        // how many browser should be started simultaneous
        concurrency: Infinity
    };
};

module.exports = {
    getConfig: getConfig,
    appRoot: appRoot
};