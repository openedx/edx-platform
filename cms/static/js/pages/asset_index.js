(function(define) {
    'use strict';

    define(
        ['js/factories/asset_index', 'common/js/utils/page_factory'],
        function(AssetIndexFactory, invokePageFactory) {
            invokePageFactory('AssetIndexFactory', AssetIndexFactory);
        }
    );
}).call(this, define || RequireJS.define);

