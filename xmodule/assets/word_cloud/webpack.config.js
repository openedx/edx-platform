/* eslint-env node */

'use strict';

var path = require('path');

module.exports = {
    entry: {
        word_cloud: 'word_cloud',
    },

    output: {
        path: path.resolve(__dirname, 'public/js'),
        filename: '[name].js',
    },

    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                use: 'babel-loader',
            },
            {
                test: /d3.min/,
                use: [
                    'babel-loader',
                    {
                        loader: 'exports-loader',
                        options: {
                            d3: true,
                        },
                    },
                ],
            },
        ],
    },

    resolve: {
        modules: [
            path.resolve(__dirname, 'src/js'),
            path.resolve(__dirname, '../../../../../../node_modules'),
        ],
        alias: {
            'edx-ui-toolkit': 'edx-ui-toolkit/src/',  // @TODO: some paths in toolkit are not valid relative paths
        },
        extensions: ['.js', '.jsx', '.json'],
    },

    externals: {
        gettext: 'gettext',
        canvas: 'canvas',
        jquery: 'jQuery',
        $: 'jQuery',
        underscore: '_',
    },
};
