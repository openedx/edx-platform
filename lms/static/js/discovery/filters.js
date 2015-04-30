;(function (define) {

define([
    'backbone',
    'js/discovery/filter'
], function (Backbone, Filter) {
    'use strict';

    return Backbone.Collection.extend({

        model: Filter,
        url: '',

        initialize: function () {
            this.bind('remove', this.onModelRemoved, this);
        },

        onModelRemoved: function (model, collection, options) {
            model.cleanModelView();
        },

        getQueryModel: function() {
            return this.findWhere({'type': 'search_string'});
        }
    });

});


})(define || RequireJS.define);
