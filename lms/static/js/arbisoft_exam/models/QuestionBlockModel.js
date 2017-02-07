;(function (define) {
    'use strict';
    define([
            'jquery',
            'backbone'
        ],
        function($, Backbone) {
            return Backbone.Model.extend({
                defaults: {
                    id: '0',
                    content: ''
                }
            });
        }
    );
}).call(this, define || RequireJS.define);



