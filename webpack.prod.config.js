/* eslint-env node */

'use strict';

var Merge = require('webpack-merge');
var path = require('path');
var webpack = require('webpack');

var ExtractTextPlugin = require('extract-text-webpack-plugin');
var extractSass = new ExtractTextPlugin({
    filename: 'css/[name].[contenthash].css'
});

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
    ],
    module: {
        rules: [
            {
                test: /(.scss|.css)$/,
                include: [
                    /paragon/,
                    /font-awesome/
                ],
                use: extractSass.extract({
                    use: [{
                        loader: 'css-loader',
                        options: {
                            modules: true,
                            localIdentName: '[name]__[local]___[hash:base64:5]'
                        }
                    }, {
                        loader: 'sass-loader',
                        options: {
                            data: '$base-rem-size: 0.625; @import "paragon-reset";',
                            includePaths: [
                                path.join(__dirname, './node_modules/@edx/paragon/src/utils'),
                                path.join(__dirname, './node_modules/')
                            ]
                        }
                    }],
                    fallback: 'style-loader'
                })
            }
        ]
    }
});
