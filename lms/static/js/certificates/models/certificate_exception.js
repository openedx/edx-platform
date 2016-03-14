// Backbone.js Application Model: CertificateWhitelist
/*global define, RequireJS */

;(function(define){
    'use strict';

    define([
            'underscore',
            'underscore.string',
            'backbone',
            'gettext'
        ],

        function(_, str, Backbone, gettext){

            return Backbone.Model.extend({
                idAttribute: 'id',

                defaults: {
                    user_id: '',
                    user_name: '',
                    user_email: '',
                    created: '',
                    certificate_generated: '',
                    notes: ''
                },

               url: function() {
                    return this.get('url');
                },

                validate: function(attrs){
                    if (!_.str.trim(attrs.user_name) && !_.str.trim(attrs.user_email)) {
                        return gettext('Student username/email field is required and can not be empty. ' +
                            'Kindly fill in username/email and then press "Add to Exception List" button.');
                    }

                }
            });
        }
    );
}).call(this, define || RequireJS.define);