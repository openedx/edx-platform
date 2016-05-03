// Karma config for common-requirejs suite.
// Docs in common/static/common/js/karma.common.conf.js

/* jshint node: true */
/*jshint -W079 */

'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var files = {
    libraryFiles: [
        {pattern: 'js/vendor/jquery.min.js'},
        {pattern: 'js/vendor/jasmine-imagediff.js'},
        {pattern: 'js/libs/jasmine-stealth.js'},
        {pattern: 'js/libs/jasmine-waituntil.js'},
        {pattern: 'js/libs/jasmine-extensions.js'},
        {pattern: 'js/vendor/jquery.simulate.js'},
        {pattern: 'js/vendor/jquery.truncate.js'},
        {pattern: 'common/js/vendor/underscore.js'},
        {pattern: 'common/js/vendor/underscore.string.js'},
        {pattern: 'common/js/vendor/backbone.js'},
        {pattern: 'js/vendor/backbone.paginator.min.js'},
        {pattern: 'js/vendor/jquery.timeago.js'},
        {pattern: 'js/vendor/URI.min.js'},
        {pattern: 'coffee/src/ajax_prefix.js'},
        {pattern: 'js/test/add_ajax_prefix.js'},
        {pattern: 'js/test/i18n.js'},
        {pattern: 'coffee/src/jquery.immediateDescendents.js'},
        {pattern: 'js/vendor/requirejs/text.js'},
        {pattern: 'js/vendor/sinon-1.17.0.js'},
        {pattern: 'common/js/utils/require-serial.js', included: true}
    ],

    sourceFiles: [
        {pattern: 'common/js/**/!(*spec).js'}
    ],

    specFiles: [
        {pattern: 'common/js/spec/**/*spec.js'}
    ],

    fixtureFiles: [
        {pattern: 'common/templates/**/*.*'}
    ],

    runFiles: [
        {pattern: 'common/js/spec/main_requirejs.js', included: true}
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
