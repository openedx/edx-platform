// Common JavaScript tests, using RequireJS.
//
//
// To run all the tests and print results to the console:
//
//   karma start lms/static/js_test_coffee.js
//
//
// To run the tests for debugging: Debugging can be done in any browser but Chrome's developer console debugging experience is best.
//
//   karma start lms/static/js_test_coffee.js --browsers=BROWSER --single-run=false
//
//
// To run the tests with coverage and junit reports:
//
//   karma start lms/static/js_test_coffee.js --browsers=BROWSER --coverage --junitreportpath=<xunit_report_path> --coveragereportpath=<report_path>
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
    var defaultReporters = ['dots', 'junit'];
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
    if(!filepath) {
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
        reporters:[
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


module.exports = function(config) {
    config.set({

        // base path that will be used to resolve all patterns (eg. files, exclude)
        basePath: '',


        // frameworks to use
        // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
        frameworks: ['jasmine-jquery', 'jasmine'],


        // list of files / patterns to load in the browser
        files: [
            // include vendor js files but don't add a <script> tag for each
            'xmodule_js/common_static/js/vendor/jquery.min.js',
            'xmodule_js/common_static/js/test/i18n.js',
            'xmodule_js/common_static/coffee/src/ajax_prefix.js',
            'xmodule_js/common_static/js/src/logger.js',
            'xmodule_js/common_static/js/vendor/underscore-min.js',
            'xmodule_js/common_static/js/vendor/jasmine-imagediff.js',
            'xmodule_js/common_static/js/vendor/requirejs/require.js',
            'js/RequireJS-namespace-undefine.js',
            'xmodule_js/common_static/js/vendor/jquery-ui.min.js',
            'xmodule_js/common_static/js/vendor/jquery.cookie.js',
            'xmodule_js/common_static/js/vendor/flot/jquery.flot.js',
            'xmodule_js/common_static/js/vendor/moment.min.js',
            'xmodule_js/common_static/js/vendor/moment-with-locales.min.js',
            'xmodule_js/common_static/js/vendor/CodeMirror/codemirror.js',
            'xmodule_js/common_static/js/vendor/URI.min.js',
            'xmodule_js/common_static/coffee/src/jquery.immediateDescendents.js',
            'xmodule_js/common_static/js/xblock/*.js',
            'xmodule_js/common_static/coffee/src/xblock/*.js',
            'moment_requirejs.js',
            'xmodule_js/src/capa/*.js',
            'xmodule_js/src/video/*.js',
            'xmodule_js/src/xmodule.js',

            // include src js
            //- coffee/src

            'coffee/src/**/*.js',

            // include spec js
            //- coffee/spec

            //'coffee/spec/helper.js',
            'coffee/spec/**/*.js',


            // include fixtures
            //- coffee/fixtures

            'coffee/fixtures/**/*.*',

            // override fixture path and other config.
            'test_config.js'
        ],


        // list of files to exclude
        exclude: [
        ],


        // preprocess matching files before serving them to the browser
        // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
        preprocessors: {
            'coffee/src/**/*.js': ['coverage']
        },


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
        logLevel: config.LOG_INFO,


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