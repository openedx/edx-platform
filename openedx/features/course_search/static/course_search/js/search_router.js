(function(define) {
    'use strict';

    define(['backbone'], function(Backbone) {
        return Backbone.Router.extend({
            routes: {
                'search/:query': 'search'
            },
            search: function(query) {
                this.trigger('search', query);
            }
        });
    });
}(define || RequireJS.define));
