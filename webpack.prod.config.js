/* eslint-env node */

'use strict';

var Merge = require('webpack-merge');
var webpack = require('webpack');

var commonConfig = require('./webpack.common.config.js');

module.exports = Merge.smart(commonConfig, {
    output: {
        filename: '[name].[chunkhash].js'
    },
    devtool: false,
    plugins: [
        new webpack.DefinePlugin({
            'process.env.NODE_ENV': JSON.stringify('production')
        }),
        new webpack.LoaderOptionsPlugin({  // This may not be needed; legacy option for loaders written for webpack 1
            minimize: true
        }),
        new webpack.optimize.UglifyJsPlugin()
    ]
});
