;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
], function ($, _, Backbone, gettext) {

   'use strict';

    return Backbone.View.extend({

        // these should be defined by subclasses
        el: '',
        contentElement: '',
        resultsTemplateId: '',
        loadingTemplateId: '',
        errorTemplateId: '',
        events: {},
        spinner: '.search-load-next .icon',
        SearchItemView: function () {},

        initialize: function () {
            this.$contentElement = $(this.contentElement);
            this.resultsTemplate = _.template($(this.resultsTemplateId).html());
            this.loadingTemplate = _.template($(this.loadingTemplateId).html());
            this.errorTemplate = _.template($(this.errorTemplateId).html());
        },

        render: function () {
            this.$el.html(this.resultsTemplate({
                totalCount: this.collection.totalCount,
                totalCountMsg: this.totalCountMsg(),
                pageSize: this.collection.pageSize,
                hasMoreResults: this.collection.hasNextPage()
            }));
            this.renderItems();
            this.$el.find(this.spinner).hide();
            this.$contentElement.hide();
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
            var latest = this.collection.latestModels();
            var items = latest.map(function (result) {
                var item = new this.SearchItemView({ model: result });
                return item.render().el;
            }, this);
            this.$el.find('ol').append(items);
        },

        totalCountMsg: function () {
            var fmt = ngettext('%s result', '%s results', this.collection.totalCount);
            return interpolate(fmt, [this.collection.totalCount]);
        },

        clear: function () {
            this.$el.hide().empty();
            this.$contentElement.show();
        },

        showLoadingMessage: function () {
            this.$el.html(this.loadingTemplate());
            this.$el.show();
            this.$contentElement.hide();
        },

        showErrorMessage: function () {
            this.$el.html(this.errorTemplate());
            this.$el.show();
            this.$contentElement.hide();
        },

        loadNext: function (event) {
            event && event.preventDefault();
            this.$el.find(this.spinner).show();
            this.trigger('next');
            return false;
        }

    });

});


})(define || RequireJS.define);
