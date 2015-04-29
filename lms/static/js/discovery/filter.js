;(function (define) {

define(['backbone'], function (Backbone) {
    'use strict';

    return Backbone.Model.extend({
        defaults: {
            query: '',
            type: 'query'
        },

        cleanModelView: function() {
            this.destroy();
        }
    });

});

})(define || RequireJS.define);
