;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
    'js/search/views/search_item_view'
], function ($, _, Backbone, gettext, SearchItemView) {

   'use strict';

    return Backbone.View.extend({

        el: '#courseware-search-results',
        events: {
            'click .search-load-next': 'loadNext'
        },
        spinner: '.icon',

        initialize: function () {
            this.courseName = this.$el.attr('data-course-name');
            this.$courseContent = $('#course-content');
            this.listTemplate = _.template($('#search_list-tpl').html());
            this.loadingTemplate = _.template($('#search_loading-tpl').html());
            this.errorTemplate = _.template($('#search_error-tpl').html());
            this.collection.on('search', this.render, this);
            this.collection.on('next', this.renderNext, this);
            this.collection.on('error', this.showErrorMessage, this);
        },

        render: function () {
            this.$el.html(this.listTemplate({
                totalCount: this.collection.totalCount,
                totalCountMsg: this.totalCountMsg(),
                pageSize: this.collection.pageSize,
                hasMoreResults: this.collection.hasNextPage()
            }));
            this.renderItems();
            this.$courseContent.hide();
            this.$el.show();
            return this;
        },

        renderNext: function () {
            // total count may have changed
            this.$el.find('.search-count').text(this.totalCountMsg());
            this.renderItems();
            if (! this.collection.hasNextPage()) {
                this.$el.find('.search-load-next').remove();
            }
            this.$el.find(this.spinner).hide();
        },

        renderItems: function () {
            var items = this.collection.map(function (result) {
                var item = new SearchItemView({ model: result });
                return item.render().el;
            });
            this.$el.find('.search-results').append(items);
        },

        totalCountMsg: function () {
            var fmt = ngettext('%s result', '%s results', this.collection.totalCount);
            return interpolate(fmt, [this.collection.totalCount]);
        },

        clear: function () {
            this.$el.hide().empty();
            this.$courseContent.show();
        },

        showLoadingMessage: function () {
            this.$el.html(this.loadingTemplate());
            this.$el.show();
            this.$courseContent.hide();
        },

        showErrorMessage: function () {
            this.$el.html(this.errorTemplate());
            this.$el.show();
            this.$courseContent.hide();
        },

        loadNext: function (event) {
            event && event.preventDefault();
            this.$el.find(this.spinner).show();
            this.trigger('next');
        }

    });

});


})(define || RequireJS.define);
