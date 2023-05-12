(function(define) {
    'use strict';

    define(['js/api_admin/views/catalog_preview'], function(CatalogPreviewView) {
        return function(options) {
            var view = new CatalogPreviewView({
                el: '.catalog-body',
                previewUrl: options.previewUrl,
                catalogApiUrl: options.catalogApiUrl
            });
            return view.render();
        };
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
