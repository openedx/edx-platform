// Backbone.js Application Model: CertificateInvalidation
/*global define, RequireJS */

;(function(define) {
    'use strict';

    define(
        ['underscore', 'underscore.string', 'gettext', 'backbone'],

        function(_, str, gettext, Backbone) {
            return Backbone.Model.extend({
                idAttribute: 'id',

                defaults: {
                    user: '',
                    invalidated_by: '',
                    created: '',
                    notes: ''
                },

                url: function() {
                    return this.get('url');
                },

                validate: function(attrs) {
                    if (!_.str.trim(attrs.user)) {
                        // A username or email must be provided for certificate invalidation
                        return gettext('Student username/email field is required and can not be empty. ' +
                            'Kindly fill in username/email and then press "Invalidate Certificate" button.');
                    }
                }
            });
        }
    );
}).call(this, define || RequireJS.define);