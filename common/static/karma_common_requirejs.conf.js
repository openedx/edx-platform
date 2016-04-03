// Common JavaScript tests, using RequireJS.
//
//
// To run all the tests and print results to the console:
//
//   karma start common/static/karma_common_requirejs.conf.js
//
//
// To run the tests for debugging: Debugging can be done in any browser but Chrome's developer console debugging experience is best.
//
//   karma start karma_common_requirejs.conf.js --browsers=BROWSER --single-run=false
//
//
// To run the tests with coverage and junit reports:
//
//   karma start karma_common_requirejs.conf.js --browsers=BROWSER --coverage --junitreportpath=<xunit_report_path> --coveragereportpath=<report_path>
//
// where `BROWSER` could be Chrome or Firefox.
//
//

/**
 * Customize the name attribute in xml testcase element
 * @param {Object} browser
 * @param {Object} result
 * @return {String}
 */
function junitNameFormatter(browser, result) {
    return result.suite[0] + ": " + result.description;
}


/**
 * Customize the classname attribute in xml testcase element
 * @param {Object} browser
 * @param {Object} result
 * @return {String}
 */
function junitClassNameFormatter(browser, result) {
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
        defaultReporters.push('coverage')
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
    }
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
        suite: 'javascript', // suite will become the package name attribute in xml testsuite element
        useBrowserName: false,
        nameFormatter: junitNameFormatter,
        classNameFormatter: junitClassNameFormatter
    };
}


module.exports = function (config) {
    config.set({

        // base path that will be used to resolve all patterns (eg. files, exclude)
        basePath: '',
        baseUrl: '/base',


        // frameworks to use
        // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
        frameworks: ['requirejs', 'jasmine-jquery', 'jasmine'],


        // list of files / patterns to load in the browser
        files: [
            {pattern: 'js/vendor/jquery.min.js', included: false},
            {pattern: 'js/vendor/jasmine-imagediff.js', included: false},
            {pattern: 'js/libs/jasmine-stealth.js', included: false},
            {pattern: 'js/libs/jasmine-waituntil.js', included: false},
            {pattern: 'js/vendor/jquery.simulate.js', included: false},
            {pattern: 'js/vendor/jquery.truncate.js', included: false},
            {pattern: 'common/js/vendor/underscore.js', included: false},
            {pattern: 'js/vendor/underscore.string.min.js', included: false},
            {pattern: 'js/vendor/backbone-min.js', included: false},
            {pattern: 'js/vendor/backbone.paginator.min.js', included: false},
            {pattern: 'js/vendor/jquery.timeago.js', included: false},
            {pattern: 'js/vendor/URI.min.js', included: false},
            {pattern: 'coffee/src/ajax_prefix.js', included: false},
            {pattern: 'js/test/add_ajax_prefix.js', included: false},
            {pattern: 'js/test/i18n.js', included: false},
            {pattern: 'coffee/src/jquery.immediateDescendents.js', included: false},
            {pattern: 'js/vendor/requirejs/text.js', included: false},
            {pattern: 'js/vendor/sinon-1.17.0.js', included: false},

            // Paths to source JavaScript files
            {pattern: 'common/js/**/*.js', included: false},

            // Paths to spec (test) JavaScript files
            {pattern: 'common/js/spec/**/*.js', included: false},

            // Paths to fixture files
            {pattern: 'common/templates/**/*.*', included: false},

            // override fixture path and other config.
            {pattern: 'test_config.js', included: true},
            'common/js/spec/main_requirejs.js'
        ],


        // list of files to exclude
        exclude: [],


        // preprocess matching files before serving them to the browser
        // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
        //preprocessors: {
        //    'coffee/src/**/*.js': ['coverage']
        //},


        // test results reporter to use
        // possible values: 'dots', 'progress'
        // available reporters: https://npmjs.org/browse/keyword/
        //
        // karma-reporter
        reporters: reporters(config),


        coverageReporter: coverageSettings(config),


        junitReporter: junitSettings(config),


        // web server port
        port: 9876,


        // enable / disable colors in the output (reporters and logs)
        colors: true,


        // level of logging
        // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
        logLevel: config.LOG_DEBUG,


        // enable / disable watching file and executing tests whenever any file changes
        autoWatch: false,


        // start these browsers
        // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
        browsers: ['Firefox'],


        // Continuous Integration mode
        // if true, Karma captures browsers, runs the tests and exits
        singleRun: true,

        // Concurrency level
        // how many browser should be started simultaneous
        concurrency: Infinity
    })
};