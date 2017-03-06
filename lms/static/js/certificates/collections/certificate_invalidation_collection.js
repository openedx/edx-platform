// Backbone.js Application Collection: CertificateInvalidationCollection
/*global define, RequireJS */

;(function(define) {
    'use strict';

    define(
        ['backbone', 'js/certificates/models/certificate_invalidation'],

        function(Backbone, CertificateInvalidation) {
            return Backbone.Collection.extend({
                model: CertificateInvalidation,

                initialize: function(models, options) {
                    this.url = options.url;
                }
            });
        }
    );
}).call(this, define || RequireJS.define);