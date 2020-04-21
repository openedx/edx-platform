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
                'process.env.LMS_ROOT_URL': JSON.stringify('https://localhost:18000'),
                'process.env.JWT_AUTH_COOKIE_HEADER_PAYLOAD': JSON.stringify('edx-jwt-cookie-header-payload'),
                'process.env.EDXMKTG_USER_INFO_COOKIE_NAME': JSON.stringify('edx-user-info')
            })
        ],
        module: {
            rules: [
                {
                    test: /(.scss|.css)$/,
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
