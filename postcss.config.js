/* eslint-env node */

'use strict';

var autoprefixerPlugin = require('autoprefixer');
var postCssRtlCssCombinedPlugin = require('postcss-rtlcss-combined');

module.exports = {
    plugins: [
        autoprefixerPlugin,
        postCssRtlCssCombinedPlugin
    ]
};
