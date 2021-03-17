(function(define) {
    'use strict';

    define([
        'jquery',
        'underscore',
        'backbone',
        'edx-ui-toolkit/js/utils/html-utils',
        'edx-ui-toolkit/js/utils/string-utils',
        'course_search/js/views/search_item_view',
        'text!course_search/templates/search_loading.underscore',
        'text!course_search/templates/search_error.underscore'
    ], function($, _, Backbone, HtmlUtils, StringUtils, SearchItemView, searchLoadingTemplate, searchErrorTemplate) {
        return Backbone.View.extend({

            // these should be defined by subclasses
            el: '',
            contentElement: '',
            resultsTemplate: null,
            itemTemplate: null,
            loadingTemplate: searchLoadingTemplate,
            errorTemplate: searchErrorTemplate,
            events: {},
            spinner: '.search-load-next .icon',

            initialize: function() {
                this.$contentElement = this.contentElement ? $(this.contentElement) : $([]);
            },

            render: function() {
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.resultsTemplate)({
                    totalCount: this.collection.totalCount,
                    totalCountMsg: this.totalCountMsg(),
                    pageSize: this.collection.pageSize,
                    hasMoreResults: this.collection.hasNextPage(),
                    searchTerm: this.collection.searchTerm
                }));
                this.renderItems();
                this.$el.find(this.spinner).hide();
                this.showResults();
                return this;
            },

            renderNext: function() {
                // total count may have changed
                this.$el.find('.search-count').text(this.totalCountMsg());
                this.renderItems();
                if (!this.collection.hasNextPage()) {
                    this.$el.find('.search-load-next').remove();
                }
                this.$el.find(this.spinner).hide();
            },

            renderItems: function() {
                var latest = this.collection.latestModels();
                var items = latest.map(function(result) {
                    var item = new SearchItemView({
                        model: result,
                        template: this.itemTemplate
                    });
                    return item.render().el;
                }, this);
                // xss-lint: disable=javascript-jquery-append
                this.$el.find('ol').append(items);
            },

            totalCountMsg: function() {
                var fmt = ngettext(
                    '{total_results} result found for "{search_term}"',
                    '{total_results} results found for "{search_term}"',
                    this.collection.totalCount
                );
                return StringUtils.interpolate(fmt, {
                    total_results: this.collection.totalCount,
                    search_term: this.collection.searchTerm
                });
            },

            clear: function() {
                this.$el.hide().empty();
                this.$contentElement.show();
            },

            showResults: function() {
                this.$el.show();
                this.$contentElement.hide();
            },

            showLoadingMessage: function() {
                // Empty any previous loading/error message
                $('#loading-message').html('');
                $('#error-message').html('');

                // Show the loading message
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.loadingTemplate)());

                // Show the results
                this.showResults();
            },

            showErrorMessage: function() {
                HtmlUtils.setHtml(
                    this.$el,
                    HtmlUtils.template(this.errorTemplate)({
                        errorMessage: this.collection.errorMessage
                    }));
                this.showResults();
            },

            loadNext: function(event) {
                if (event) {
                    event.preventDefault();
                }
                this.$el.find(this.spinner).show();
                this.trigger('next');
                return false;
            }

        });
    });
}(define || RequireJS.define));
