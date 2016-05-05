// Karma config for cms suite.
// Docs in common/static/common/js/karma.common.conf.js

/* jshint node: true */
/*jshint -W079 */
'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var options = {

    includeCommonFiles: true,

    libraryFiles: [],

    sourceFiles: [
        {pattern: 'coffee/src/**/!(*spec).js'},
        {pattern: 'js/**/!(*spec|djangojs).js'}
    ],

    specFiles: [
        {pattern: 'coffee/spec/**/*spec.js'},
        {pattern: 'js/certificates/spec/**/*spec.js'},
        {pattern: 'js/spec/**/*spec.js'}
    ],

    fixtureFiles: [
        {pattern: 'coffee/fixtures/**/*.underscore'},
        {pattern: 'templates/**/*.underscore'}
    ],

    runFiles: [
        {pattern: 'coffee/spec/main.js', included: true}
    ]
};

module.exports = function (config) {
    configModule.configure(config, options);
};
