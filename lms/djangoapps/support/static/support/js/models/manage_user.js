(function(define) {
    'use strict';
    define(['backbone', 'underscore'], function(Backbone, _) {
        return Backbone.Model.extend({

            initialize: function(options) {
                this.user = options.user || '';
                this.baseUrl = options.baseUrl;
            },

            url: function() {
                return this.baseUrl + this.user;
            },
            disableAccount: function() {
                return $.ajax({
                    url: this.url(),
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        username_or_email: this.get('username')
                    }),
                    success: _.bind(function(response) {
                        this.set('response', response.success_msg);
                        this.set('status', response.status);
                    }, this)
                });
            }
        });
    });
}).call(this, define || RequireJS.define);
