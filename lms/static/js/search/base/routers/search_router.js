(function(define) {
    define(['backbone'], function(Backbone) {
        'use strict';

        return Backbone.Router.extend({
            routes: {
                'search/:query': 'search'
            },
            search: function(query) {
                this.trigger('search', query);
            }
        });
    });
})(define || RequireJS.define);
