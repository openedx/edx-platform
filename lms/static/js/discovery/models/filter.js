(function(define) {
    define(['backbone'], function(Backbone) {
        'use strict';

        return Backbone.Model.extend({
            // idAttribute: 'type',
            idAttribute: function() {
                return this.get('type') + ':' + this.get('query');
            },
            defaults: {
                type: 'search_query',
                query: '',
                name: ''
            }
        });
    });
}(define || RequireJS.define));
