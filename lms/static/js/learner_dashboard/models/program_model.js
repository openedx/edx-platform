/**
 * Model for Course Programs.
 */
(function (define) {
    'use strict';
    define([
            'backbone'
        ], 
        function (Backbone) {
        return Backbone.Model.extend({
            initialize: function(data) {
                if (data){
                    this.set({
                        name: data.name,
                        category: data.category,
                        subtitle: data.subtitle,
                        organizations: data.organizations,
                        marketingUrl: data.marketing_url
                    });
                }
            }
        });
    });
}).call(this, define || RequireJS.define);
