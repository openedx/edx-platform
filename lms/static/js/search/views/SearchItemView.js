;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext'
], function ($, _, Backbone, gettext) {
   'use strict';

    return Backbone.View.extend({

        tagName: 'li',
        className: 'search-results-item',
        attributes: {
            'role': 'region',
            'aria-label': 'search result'
        },

        initialize: function () {
            this.tpl = _.template($('#search_item-tpl').html());
        },

        render: function () {
            this.$el.html(this.tpl(this.model.attributes));
            return this;
        }
    });

});

})(define || RequireJS.define);
