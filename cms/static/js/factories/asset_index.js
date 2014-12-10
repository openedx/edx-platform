define([
    'jquery', 'js/collections/asset', 'js/views/assets', 'jquery.fileupload'
], function($, AssetCollection, AssetsView) {
    'use strict';
    return function (assetCallbackUrl) {
        var assets = new AssetCollection(),
            assetsView;

        assets.url = assetCallbackUrl;
        assetsView = new AssetsView({collection: assets, el: $('.assets-wrapper')});
        assetsView.render();
    };
});
