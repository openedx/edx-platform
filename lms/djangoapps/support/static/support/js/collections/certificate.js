;(function (define) {
    'use strict';
    define(['backbone', 'support/js/models/certificate'],
        function(Backbone, CertModel) {
            return Backbone.Collection.extend({
                model: CertModel,

                initialize: function(options) {
                    this.userQuery = options.userQuery || '';
                },

                setUserQuery: function(userQuery) {
                    this.userQuery = userQuery;
                },

                url: function() {
                    return '/certificates/search?query=' + this.userQuery;
                }
            });
    });
}).call(this, define || RequireJS.define);
