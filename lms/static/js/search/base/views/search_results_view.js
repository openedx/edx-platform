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
            this.showResults();
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

        showResults: function() {
            this.$el.show();
            this.$contentElement.hide();
        },

        showLoadingMessage: function () {
            this.doCleanup();
            this.$el.html(this.loadingTemplate());
            this.showResults();
        },

        showErrorMessage: function () {
            this.$el.html(this.errorTemplate());
            this.showResults();
        },

        doCleanup: function () {
            // Empty any loading/error message and empty the el
            // Bookmarks share the same container element, So we are doing
            // this to ensure that elements are in clean/initial state
            $('#loading-message').html('');
            $('#error-message').html('');
            this.$el.html('');
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
