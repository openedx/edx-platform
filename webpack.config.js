/* eslint-env node */

'use strict';

var path = require('path');
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');
var StringReplace = require('string-replace-webpack-plugin');

var isProd = process.env.NODE_ENV === 'production';

var namespacedRequireFiles = [
    path.resolve(__dirname, 'common/static/common/js/components/views/feedback_notification.js'),
    path.resolve(__dirname, 'common/static/common/js/components/views/feedback.js')
];

var wpconfig = {
    context: __dirname,

    entry: {
        CourseOutline: './openedx/features/course_experience/static/course_experience/js/CourseOutline.js',
        CourseSock: './openedx/features/course_experience/static/course_experience/js/CourseSock.js',
        WelcomeMessage: './openedx/features/course_experience/static/course_experience/js/WelcomeMessage.js',
        Import: './cms/static/js/features/import/factories/import.js'
    },

    output: {
        path: path.resolve(__dirname, 'common/static/bundles'),
        filename: isProd ? '[name].[chunkhash].js' : '[name].js',
        libraryTarget: 'window'
    },

    devtool: isProd ? false : 'source-map',

    plugins: [
        new webpack.NoEmitOnErrorsPlugin(),
        new webpack.NamedModulesPlugin(),
        new webpack.DefinePlugin({
            'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')
        }),
        new webpack.LoaderOptionsPlugin({
            debug: !isProd
        }),
        new BundleTracker({
            path: process.env.STATIC_ROOT_CMS,
            filename: 'webpack-stats.json'
        }),
        new BundleTracker({
            path: process.env.STATIC_ROOT_LMS,
            filename: 'webpack-stats.json'
        }),
        new webpack.ProvidePlugin({
            _: 'underscore',
            $: 'jquery',
            jQuery: 'jquery',
            'window.jQuery': 'jquery'
        })
    ],

    module: {
        rules: [
            {
                test: namespacedRequireFiles,
                loader: StringReplace.replace(
                    ['babel-loader'],
                    {
                        replacements: [
                            {
                                pattern: /\(function ?\(define\) ?\{/,
                                replacement: function() { return ''; }
                            },
                            {
                                pattern: /\}\)\.call\(this, define \|\| RequireJS\.define\);/,
                                replacement: function() { return ''; }
                            }
                        ]
                    }
                )
            },
            {
                test: /\.js$/,
                exclude: [
                    /node_modules/,
                    namespacedRequireFiles
                ],
                use: 'babel-loader'
            },
            {
                test: /\.coffee$/,
                exclude: /node_modules/,
                use: 'coffee-loader'
            },
            {
                test: /\.underscore$/,
                use: 'raw-loader'
            },
            {
                // This file is used by both RequireJS and Webpack and depends on window globals
                // This is a dirty hack and shouldn't be replicated for other files.
                test: path.resolve(__dirname, 'cms/static/cms/js/main.js'),
                use: {
                    loader: 'imports-loader',
                    options: {
                        AjaxPrefix:
                            'exports-loader?this.AjaxPrefix!../../../../common/static/coffee/src/ajax_prefix.coffee'
                    }
                }
            }
        ]
    },

    resolve: {
        extensions: ['.js', '.json', '.coffee'],
        alias: {
            'edx-ui-toolkit': 'edx-ui-toolkit/src/',  // @TODO: some paths in toolkit are not valid relative paths
            'jquery.ui': 'jQuery-File-Upload/js/vendor/jquery.ui.widget.js',
            jquery: 'jquery/src/jquery'  // Use the non-dist form of jQuery for better debugging + optimization
        },
        modules: [
            'node_modules',
            'common/static/js/vendor/'
        ]
    },

    resolveLoader: {
        alias: {
            text: 'raw-loader'  // Compatibility with RequireJSText's text! loader, uses raw-loader under the hood
        }
    },

    externals: {
        backbone: 'Backbone',
        gettext: 'gettext',
        jquery: 'jQuery',
        logger: 'Logger',
        underscore: '_',
        URI: 'URI'
    },

    watchOptions: {
        poll: true
    }
};

if (isProd) {
    wpconfig.plugins = wpconfig.plugins.concat([
        new webpack.LoaderOptionsPlugin({  // This may not be needed; legacy option for loaders written for webpack 1
            minimize: true
        }),
        new webpack.optimize.UglifyJsPlugin()
    ]);
}

module.exports = wpconfig;
