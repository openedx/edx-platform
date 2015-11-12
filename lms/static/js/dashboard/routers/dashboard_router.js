;(function (define) {
    'use strict';

    define(['backbone'], function (Backbone) {
        return Backbone.Router.extend({
            routes: {
                'courses/:tab': 'goToTab'
            },
            goToTab: function (tab) {
                this.trigger('goToTab', tab);
            }
        });
    });

})(define || RequireJS.define);
