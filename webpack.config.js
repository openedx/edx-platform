/* eslint-env node */

'use strict';

var path = require('path');
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');

var isProd = process.env.NODE_ENV === 'production';

var wpconfig = {
    context: __dirname,

    entry: {
        CourseOutline: './openedx/features/course_experience/static/course_experience/js/CourseOutline.js'
    },

    output: {
        path: path.resolve(__dirname, 'common/static/bundles'),
        filename: isProd ? '[name].[chunkhash].js' : '[name].js',
        libraryTarget: 'window'
    },

    devtool: isProd ? false : 'eval-source-map',

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
            path: process.env.STATIC_ROOT,
            filename: 'webpack-stats.json'
        })
    ],

    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: 'babel-loader'
            }
        ]
    },

    resolve: {
        extensions: ['.js', '.json']
    },

    watchOptions: {
        poll: true
    }
};

if (isProd) {
    wpconfig.plugins = wpconfig.plugins.concat([
        new webpack.LoaderOptionsPlugin({
            minimize: true
        }),
        new webpack.optimize.UglifyJsPlugin()
    ]);
}

module.exports = wpconfig;
