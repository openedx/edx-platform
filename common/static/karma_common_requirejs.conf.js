// Karma config for common-requirejs suite.
// Docs in common/static/common/js/karma.common.conf.js

/* jshint node: true */
/*jshint -W079 */

'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var files = {
    libraryFiles: [
    {pattern: 'js/vendor/jquery.min.js', included: false},
    {pattern: 'js/vendor/jasmine-imagediff.js', included: false},
    {pattern: 'js/libs/jasmine-stealth.js', included: false},
    {pattern: 'js/libs/jasmine-waituntil.js', included: false},
    {pattern: 'js/libs/jasmine-extensions.js', included: false},
    {pattern: 'js/vendor/jquery.simulate.js', included: false},
    {pattern: 'js/vendor/jquery.truncate.js', included: false},
    {pattern: 'common/js/vendor/underscore.js', included: false},
    {pattern: 'common/js/vendor/underscore.string.js', included: false},
    {pattern: 'common/js/vendor/backbone.js', included: false},
    {pattern: 'js/vendor/backbone.paginator.min.js', included: false},
    {pattern: 'js/vendor/jquery.timeago.js', included: false},
    {pattern: 'js/vendor/URI.min.js', included: false},
    {pattern: 'coffee/src/ajax_prefix.js', included: false},
    {pattern: 'js/test/add_ajax_prefix.js', included: false},
    {pattern: 'js/test/i18n.js', included: false},
    {pattern: 'coffee/src/jquery.immediateDescendents.js', included: false},
    {pattern: 'js/vendor/requirejs/text.js', included: false},
    {pattern: 'js/vendor/sinon-1.17.0.js', included: false},
    {pattern: 'common/js/utils/require-serial.js', included: true}
    ],

    sourceFiles: [
    {pattern: 'common/js/**/!(*spec).js', included: false}
    ],

    specFiles: [
    {pattern: 'common/js/spec/**/*spec.js', included: false}
    ],

    fixtureFiles: [
    {pattern: 'common/templates/**/*.*', included: false}
    ],

    runAndConfigFiles: [
    {pattern: path.join(configModule.appRoot, 'common/static/common/js/jasmine.common.conf.js'), included: true},
    'common/js/spec/main_requirejs.js'
    ]
};

var normalizePathsForCoverageFunc = function (appRoot, pattern) {
    return path.join(appRoot, '/common/static/' + pattern);
};

module.exports = function (config) {
    configModule.configure({
        config: config,
        files: files,
        normalizePathsForCoverageFunc: normalizePathsForCoverageFunc
    });
};
