var edx = edx || {};

(function ($, _, Backbone, gettext) {
   'use strict';

    edx.search = edx.search || {};

    edx.search.Item = Backbone.View.extend({
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

})(jQuery, _, Backbone, gettext);
