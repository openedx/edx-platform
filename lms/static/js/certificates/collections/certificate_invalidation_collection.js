// Backbone.js Application Collection: CertificateInvalidationCollection
/*global define, RequireJS */

;(function(define) {
    'use strict';

    define(
        ['backbone', 'js/certificates/models/certificate_invalidation'],

        function(Backbone, CertificateInvalidation) {
            return Backbone.Collection.extend({
                model: CertificateInvalidation
            });
        }
    );
}).call(this, define || RequireJS.define);