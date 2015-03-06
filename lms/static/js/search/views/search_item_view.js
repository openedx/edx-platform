;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
    'logger'
], function ($, _, Backbone, gettext, Logger) {
   'use strict';

    return Backbone.View.extend({

        tagName: 'li',
        className: 'search-results-item',
        attributes: {
            'role': 'region',
            'aria-label': 'search result'
        },

        events: {
            'click .search-results-item a': 'logSearchItem',
        },

        initialize: function () {
            var template_name = (this.model.attributes.content_type === "Sequence") ? '#search_item_seq-tpl' : '#search_item-tpl';
            this.tpl = _.template($(template_name).html());
        },

        render: function () {
            this.$el.html(this.tpl(this.model.attributes));
            return this;
        },

        /**
         * Redirect to a URL.  Mainly useful for mocking out in tests.
         * @param  {string} url The URL to redirect to.
         */
        redirect: function(url) {
            window.location.href = url;
        },

        logSearchItem: function(event) {
            event.preventDefault();
            var self = this;
            var target = this.model.id;
            var link = $(event.target).attr('href');
            var collection = this.model.collection;
            var page = collection.page;
            var pageSize = collection.pageSize;
            var searchTerm = collection.searchTerm;
            var index = collection.indexOf(this.model);
            Logger.log("edx.course.search.result_selected",
                {
                    "search_term": searchTerm,
                    "result_position": (page * pageSize + index),
                    "result_link": target
                }).always(function() {
                    self.redirect(link);
                });
        }
    });

});

})(define || RequireJS.define);

