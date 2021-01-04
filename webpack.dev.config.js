/* eslint-env node */

'use strict';

var Merge = require('webpack-merge');
var path = require('path');
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
                'process.env.NODE_ENV': JSON.stringify('development')
            })
        ],
        module: {
            rules: [
                {
                    test: /.scss$/,
                    include: [
                        /paragon/,
                        /font-awesome/
                    ],
                    use: [
                        'style-loader',
                        {
                            loader: 'css-loader',
                            options: {
                                sourceMap: true,
                                modules: true,
                                localIdentName: '[name]__[local]'
                            }
                        },
                        {
                            loader: 'sass-loader',
                            options: {
                                data: '$base-rem-size: 0.625; @import "paragon-reset";',
                                includePaths: [
                                    path.join(__dirname, './node_modules/@edx/paragon/src/utils'),
                                    path.join(__dirname, './node_modules/')
                                ],
                                sourceMap: true
                            }
                        }
                    ]
                }
            ]
        },
        watchOptions: {
            ignored: [/node_modules/, /\.git/]
        }
    }
}));
