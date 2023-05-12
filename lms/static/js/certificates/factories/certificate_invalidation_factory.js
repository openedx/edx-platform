// Backbone.js Page Object Factory: Certificate Invalidation Factory
/* global define, RequireJS */

(function(define) {
    'use strict';

    define(
        [
            'js/certificates/views/certificate_invalidation_view',
            'js/certificates/collections/certificate_invalidation_collection'
        ],
        function(CertificateInvalidationView, CertificateInvalidationCollection) {
            // eslint-disable-next-line camelcase
            return function(certificate_invalidation_collection_json, certificate_invalidation_url) {
                /* eslint-disable-next-line camelcase, no-var */
                var certificate_invalidation_collection = new CertificateInvalidationCollection(
                    JSON.parse(certificate_invalidation_collection_json), {
                        parse: true,
                        canBeEmpty: true,
                        // eslint-disable-next-line camelcase
                        url: certificate_invalidation_url
                    }
                );

                /* eslint-disable-next-line camelcase, no-var */
                var certificate_invalidation_view = new CertificateInvalidationView({
                    // eslint-disable-next-line camelcase
                    collection: certificate_invalidation_collection
                });

                // eslint-disable-next-line camelcase
                certificate_invalidation_view.render();
            };
        }
    );
}).call(this, define || RequireJS.define);
