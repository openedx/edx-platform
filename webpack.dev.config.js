/* eslint-env node */

'use strict';

var Merge = require('webpack-merge');
var webpack = require('webpack');
var _ = require('underscore');

var commonConfig = require('./webpack.common.config.js');

module.exports = _.values(Merge.smart(commonConfig, {
    web: {
        output: {
            filename: '[name].js'
        },
        devtool: 'source-map',
        plugins: [
            new webpack.LoaderOptionsPlugin({
                debug: true
            }),
            new webpack.DefinePlugin({
                'process.env.NODE_ENV': JSON.stringify('development'),
                'process.env.JS_ENV_EXTRA_CONFIG': process.env.JS_ENV_EXTRA_CONFIG
            })
        ],
        watchOptions: {
            ignored: [/node_modules/, /\.git/]
        }
    }
}));
