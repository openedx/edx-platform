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
                'process.env.NODE_ENV': JSON.stringify('development'),
                'process.env.JS_ENV_EXTRA_CONFIG': process.env.JS_ENV_EXTRA_CONFIG || '{}',
                'CAPTIONS_CONTENT_TO_REPLACE': JSON.stringify(process.env.CAPTIONS_CONTENT_TO_REPLACE || ''),
                'CAPTIONS_CONTENT_REPLACEMENT': JSON.stringify(process.env.CAPTIONS_CONTENT_REPLACEMENT || '')
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
                                modules: {
                                     localIdentName: '[name]__[local]'
                                }
                            }
                        },
                        {
                            loader: 'sass-loader',
                            options: {
                                sassOptions: {
                                    includePaths: [
                                        path.join(__dirname, './node_modules/@openedx/paragon/scss'),
                                        path.join(__dirname, './node_modules/@openedx/paragon/src/utils'),
                                        path.join(__dirname, './node_modules/')
                                    ]
                                },
                                sourceMap: true
                            }
                        }
                    ]
                }
            ]
        },
        watchOptions: {
            ignored: ['/node_modules/', '/\.git/']
        }
    }
}));
