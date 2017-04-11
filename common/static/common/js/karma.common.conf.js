// Common settings and helpers for setting up Karma config.
//
// To run all the tests in a suite and print results to the console:
//
//   karma start <karma_config_for_suite_path>
//   E.g. karma start lms/static/karma_lms.conf.js
//
//
// To run the tests for debugging: Debugging can be done in any browser
// but Chrome's developer console debugging experience is best.
//
//   karma start <karma_config_for_suite_path> --browsers=BROWSER --single-run=false
//
//
// To run the tests with coverage and junit reports:
//
//   karma start <karma_config_for_suite_path> --browsers=BROWSER
// --coverage --junitreportpath=<xunit_report_path> --coveragereportpath=<report_path>
//
// where `BROWSER` could be Chrome or Firefox.
//
//
// Troubleshooting tips:
//
// If you get an error like: "TypeError: __cov_KBCc7ZI4xZm8W2BC5NQLDg.s is undefined",
// that means the patterns in sourceFiles and specFiles are matching the same file.
// This causes Istanbul, which is used for tracking coverage to instrument the file
// multiple times.
//
//
// If you see the error: "EMFILE, too many open files" that means the files pattern
// that has been added is matching too many files. The glob library used by Karma
// does not use graceful-fs and tries to read files simultaneously.
//

/* eslint-env node */

'use strict';

var path = require('path');
var _ = require('underscore');
var appRoot = path.join(__dirname, '../../../../');
var webpackConfig = require(path.join(appRoot, 'webpack.config.js'));

delete webpackConfig.entry;

// Files which are needed by all lms/cms suites.
var commonFiles = {
    libraryFiles: [
        {pattern: 'common/js/vendor/**/*.js'},
        {pattern: 'edx-pattern-library/js/**/*.js'},
        {pattern: 'edx-ui-toolkit/js/**/*.js'},
        {pattern: 'xmodule_js/common_static/coffee/src/**/!(*spec).js'},
        {pattern: 'xmodule_js/common_static/common/js/**/!(*spec).js'},
        {pattern: 'xmodule_js/common_static/js/**/!(*spec).js'},
        {pattern: 'xmodule_js/src/**/*.js'}
    ],

    sourceFiles: [
        {pattern: 'common/js/!(spec_helpers)/**/!(*spec).js'}
    ],

    specFiles: [
        {pattern: 'common/js/spec_helpers/**/*.js'}
    ],

    fixtureFiles: [
        {pattern: 'common/templates/**/*.underscore'}
    ]
};

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
    return 'Javascript.' + browser.name.split(' ')[0];
}


/**
 * Return array containing default and user supplied reporters
 * @param {Object} config
 * @return {Array}
 */
function reporters(config) {
    var defaultReporters = ['spec', 'junit', 'kjhtml'];
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
        includeAllSources: true,
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

/**
 * Return absolute path for files in common and xmodule_js symlink dirs.
 * @param {String} appRoot
 * @param {String} pattern
 * @return {String}
 */
// I'd like to fix the no-shadow violation on the next line, but it would break this shared conf's API.
function defaultNormalizeFunc(appRoot, pattern) {  // eslint-disable-line no-shadow
    if (pattern.match(/^common\/js/)) {
        pattern = path.join(appRoot, '/common/static/' + pattern);
    } else if (pattern.match(/^xmodule_js\/common_static/)) {
        pattern = path.join(appRoot, '/common/static/' +
            pattern.replace(/^xmodule_js\/common_static\//, ''));
    }
    return pattern;
}

function normalizePathsForCoverage(files, normalizeFunc, preprocessors) {
    var normalizeFn = normalizeFunc || defaultNormalizeFunc,
        normalizedFile,
        filesForCoverage = {};

    files.forEach(function(file) {
        if (!file.ignoreCoverage) {
            normalizedFile = normalizeFn(appRoot, file.pattern);
            if (preprocessors && preprocessors.hasOwnProperty(normalizedFile)) {
                filesForCoverage[normalizedFile] = ['coverage'].concat(preprocessors[normalizedFile]);
            } else {
                filesForCoverage[normalizedFile] = ['coverage'];
            }
        }
    });

    return filesForCoverage;
}

/**
 * Sets defaults for each file pattern.
 * RequireJS files are excluded by default.
 * Webpack files are included by default.
 * @param {Object} files
 * @return {Object}
 */
function setDefaults(files) {
    return files.map(function(f) {
        var file = _.isObject(f) ? f : {pattern: f};
        if (!file.included && !file.webpack) {
            f.included = false;
        }
        return file;
    });
}

function getBaseConfig(config, useRequireJs) {
    var getFrameworkFiles = function() {
        var files = [
            'node_modules/jquery/dist/jquery.js',
            'node_modules/jasmine-core/lib/jasmine-core/jasmine.js',
            'common/static/common/js/jasmine_stack_trace.js',
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

    // Manually prepends the framework files to the karma files array
    // bypassing the karma's framework config. This is necessary if you want
    // to add a library or framework that isn't a karma plugin. e.g. we add jasmine-jquery
    // which isn't a karma plugin. Though a karma framework for jasmine-jquery is available
    // but it's not actively maintained. In future we also wanna add jQuery at the top when
    // we upgrade to jQuery 2
    var initFrameworks = function(files) {
        getFrameworkFiles().reverse().forEach(function(f) {
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
            'karma-spec-reporter',
            'karma-webpack',
            'karma-sourcemap-loader',
            customPlugin
        ],


        // list of files to exclude
        exclude: [],

        // karma-reporter
        reporters: reporters(config),

        // Spec Reporter configuration
        specReporter: {
            maxLogLines: 5,
            showSpecTiming: true
        },


        coverageReporter: coverageSettings(config),


        junitReporter: junitSettings(config),


        // web server port
        port: 9876,


        // enable / disable colors in the output (reporters and logs)
        colors: true,


        // level of logging
        /* possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN
         || config.LOG_INFO || config.LOG_DEBUG */
        logLevel: config.LOG_INFO,


        // enable / disable watching file and executing tests whenever any file changes
        autoWatch: false,


        // start these browsers
        // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
        browsers: ['FirefoxNoUpdates'],

        customLaunchers: {
            // Firefox configuration that doesn't perform auto-updates
            FirefoxNoUpdates: {
                base: 'Firefox',
                prefs: {
                    'app.update.auto': false,
                    'app.update.enabled': false
                }
            }
        },

        // Continuous Integration mode
        // if true, Karma captures browsers, runs the tests and exits
        singleRun: config.singleRun,

        // Concurrency level
        // how many browser should be started simultaneous
        concurrency: Infinity,

        browserNoActivityTimeout: 50000,

        client: {
            captureConsole: false
        },

        webpack: webpackConfig,

        webpackMiddleware: {
            watchOptions: {
                poll: true
            }
        }
    };
}

function configure(config, options) {
    var useRequireJs = options.useRequireJs === undefined ? true : useRequireJs,
        baseConfig = getBaseConfig(config, useRequireJs);

    if (options.includeCommonFiles) {
        _.forEach(['libraryFiles', 'sourceFiles', 'specFiles', 'fixtureFiles'], function(collectionName) {
            options[collectionName] = _.flatten([commonFiles[collectionName], options[collectionName]]);
        });
    }

    var files = _.flatten(
        _.map(
            ['libraryFilesToInclude', 'libraryFiles', 'sourceFiles', 'specFiles', 'fixtureFiles', 'runFiles'],
            function(collectionName) { return options[collectionName] || []; }
        )
    );

    files.unshift(
        {pattern: path.join(appRoot, 'common/static/common/js/jasmine.common.conf.js'), included: true}
    );

    if (useRequireJs) {
        files.unshift({pattern: 'common/js/utils/require-serial.js', included: true});
    }

    // Karma sets included=true by default.
    // We set it to false by default because RequireJS should be used instead.
    files = setDefaults(files);

    var filesForCoverage = _.flatten(
        _.map(
            ['sourceFiles', 'specFiles'],
            function(collectionName) { return options[collectionName]; }
        )
    );

    // If we give symlink paths to Istanbul, coverage for each path gets tracked
    // separately. So we pass absolute paths to the karma-coverage preprocessor.
    var preprocessors = _.extend(
        {},
        options.preprocessors,
        normalizePathsForCoverage(filesForCoverage, options.normalizePathsForCoverageFunc, options.preprocessors)
    );

    config.set(_.extend(baseConfig, {
        files: files,
        preprocessors: preprocessors
    }));
}

module.exports = {
    configure: configure,
    appRoot: appRoot
};
