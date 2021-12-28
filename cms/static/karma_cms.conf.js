/* eslint-env node */

// Karma config for cms suite.
// Docs and troubleshooting tips in common/static/common/js/karma.common.conf.js

'use strict';
var path = require('path');
var configModule = require(path.join(__dirname, '../../common/static/common/js/karma.common.conf.js'));

var options = {

    includeCommonFiles: true,

    libraryFiles: [],

    libraryFilesToInclude: [
        { pattern: 'common/js/vendor/jquery.js', included: true },
        { pattern: 'common/js/vendor/jquery-migrate.js', included: true }
    ],

    // Make sure the patterns in sourceFiles and specFiles do not match the same file.
    // Otherwise Istanbul which is used for coverage tracking will cause tests to not run.
    sourceFiles: [
        { pattern: 'cms/**/!(*spec|djangojs).js' },
        { pattern: 'js/**/!(*spec|djangojs).js' },
    ],

    specFiles: [
        { pattern: 'cms/**/*spec.js' },
        { pattern: 'js/certificates/spec/**/*spec.js' },
        { pattern: 'js/spec/**/*spec.js' }
    ],

    fixtureFiles: [
        { pattern: '../templates/js/**/*.underscore' },
        { pattern: 'templates/**/*.underscore' }
    ],

    runFiles: [
        { pattern: 'cms/js/spec/main.js', included: true },
        { pattern: 'jasmine.cms.conf.js', included: true }
    ],

    preprocessors: {
        'cms/**/!(*spec|djangojs).js': ['webpack', 'sourcemap'],
        'js/**/!(*spec|djangojs).js': ['webpack', 'sourcemap'],
    },

    customPreprocessors:{
        babelSourceMap:{
          base: 'babel',
          options:{
            presets: ['react', 'es2015'],
            sourceMap: 'inline'
          },
          filename: function(file){
            return file.originalPath.replace(/\.js$/, '.es5.js');
          },
          sourceFileName: function(file){
            return file.originalPath;
          }
        },
      },
      
    webpack: { //kind of a copy of your webpack config
        devtool: 'inline-source-map', //just do inline source maps instead of the default
        module: {
            loaders: [
                { test: /\.js$/, loader: 'babel-loader' }
            ]
        }
    },
    webpackServer: {
        noInfo: true //please don't spam the console when running in karma!
    }
};

(options.sourceFiles.concat(options.specFiles))
    .filter(function (file) { return file.webpack; })
    .forEach(function (file) {
        options.preprocessors[file.pattern] = ['webpack'];
    });

module.exports = function (config) {
    configModule.configure(config, options);
};
