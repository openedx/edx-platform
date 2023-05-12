// eslint-disable-next-line no-undef
define([
    'jquery', 'js/collections/asset', 'js/views/assets', 'jquery.fileupload'
], function($, AssetCollection, AssetsView) {
    'use strict';

    return function(config) {
        // eslint-disable-next-line no-var
        var assets = new AssetCollection(),
            assetsView;

        assets.url = config.assetCallbackUrl;
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
