define(
    ['js/factories/asset_index', 'common/js/utils/page_factory', 'js/factories/base'],
    function(AssetIndexFactory, invokePageFactory) {
        'use strict';
        invokePageFactory('AssetIndexFactory', AssetIndexFactory);
    }
);
