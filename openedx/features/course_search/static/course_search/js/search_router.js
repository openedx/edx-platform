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
// eslint-disable-next-line no-undef
}(define || RequireJS.define));
