(function(define) {
    define(['backbone'], function(Backbone) {
        'use strict';

        return Backbone.Model.extend({
            idAttribute: 'type',
            defaults: {
                type: 'search_query',
                query: '',
                name: ''
            }
        });
    });
// eslint-disable-next-line no-undef
}(define || RequireJS.define));
