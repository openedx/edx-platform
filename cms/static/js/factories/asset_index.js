define([
    'jquery', 'js/collections/asset', 'js/views/assets', 'jquery.fileupload'
], function($, AssetCollection, AssetsView) {
    'use strict';
    return function(config) {
        var assets = new AssetCollection(),
            assetsView,
            urlConcatChar,
            regex;

        regex = /[?&]?([^=]+)=([^&]*)/g; // regex to test for query parameters in url
        urlConcatChar = (regex.exec(config.assetCallbackUrl) != null) ? '&' : urlConcatChar = '?';

        assets.url = config.assetCallbackUrl + urlConcatChar + 'filter_criteria=' + config.filterCriteria;
        assetsView = new AssetsView({
            collection: assets,
            el: $('.wrapper-assets'),
            uploadChunkSizeInMBs: config.uploadChunkSizeInMBs,
            maxFileSizeInMBs: config.maxFileSizeInMBs,
            maxFileSizeRedirectUrl: config.maxFileSizeRedirectUrl
        });
        assetsView.render();
    };
});
