;(function (define) {

define(['backbone'], function (Backbone) {
    'use strict';

    return Backbone.Model.extend({
        defaults: {
            query: '',
            type: 'search_string'
        },

        cleanModelView: function() {
            this.destroy();
        }
    });

});

})(define || RequireJS.define);
