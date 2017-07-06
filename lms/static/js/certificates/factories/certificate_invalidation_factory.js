// Backbone.js Page Object Factory: Certificate Invalidation Factory
/*global define, RequireJS */

;(function(define) {
    'use strict';
    define(
        [
            'js/certificates/views/certificate_invalidation_view',
            'js/certificates/collections/certificate_invalidation_collection'
        ],
        function(CertificateInvalidationView, CertificateInvalidationCollection) {

            return function(certificate_invalidation_collection_json, certificate_invalidation_url) {
                var certificate_invalidation_collection = new CertificateInvalidationCollection(
                    JSON.parse(certificate_invalidation_collection_json), {
                        parse: true,
                        canBeEmpty: true,
                        url: certificate_invalidation_url
                    }
                );

                var certificate_invalidation_view = new CertificateInvalidationView({
                    collection: certificate_invalidation_collection
                });

                certificate_invalidation_view.render();
            };

        }
    );
}).call(this, define || RequireJS.define);