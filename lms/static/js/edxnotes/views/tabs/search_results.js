;(function (define, undefined) {
'use strict';
define([
    'gettext', 'js/edxnotes/views/subview', 'js/edxnotes/views/tab_view',
    'js/edxnotes/views/search_box', 'jquery.highlight'
], function (gettext, SubView, TabView, SearchBoxView) {
    var SearchResultsView = TabView.extend({
        SubViewConstructor: SubView.extend({
            id: 'edx-notes-page-search-results',
            highlightMatchedText: true,
            templateName: 'recent-activity-item',
            render: function () {
                this.$el.html(this.template({collection: this.collection}));

                if (this.highlightMatchedText) {
                    this.$('.edx-notes-item-text').highlight(this.options.searchQuery, {
                        element: 'span',
                        className: 'edx-notes-highlight',
                        caseSensitive: false
                    });
                }
                return this;
            }
        }),

        NoResultsViewConstructor: SubView.extend({
            id: 'edx-notes-page-no-search-results',
            render: function () {
                var message = gettext('No results found for "%(query_string)s".');
                this.$el.html(interpolate(message, {
                    query_string: this.options.searchQuery
                }, true));
                return this;
            }
        }),

        tabInfo: {
            name: gettext('Search Results'),
            class_name: 'tab-search-results',
            is_closable: true
        },

        initialize: function (options) {
            _.bindAll(this, 'onBeforeSearchStart', 'onSearch', 'onSearchError');
            TabView.prototype.initialize.call(this, options);
            this.searchResults = null;
            this.searchBox = new SearchBoxView({
                el: this.$('form.search-box').get(0),
                user: this.options.user,
                courseId: this.options.courseId,
                debug: this.options.debug,
                beforeSearchStart: this.onBeforeSearchStart,
                search: this.onSearch,
                error: this.onSearchError
            });
        },

        renderContent: function () {
            return this.searchPromise.done(_.bind(function () {
                var contentView = this.getSubView();
                if (contentView) {
                    this.$('.course-info').append(contentView.render().$el);
                }
            }, this));
        },

        getSubView: function () {
            var collection = this.getCollection();
            if (collection) {
                if (collection.length) {
                    return new this.SubViewConstructor({
                        collection: collection,
                        searchQuery: this.searchResults.searchQuery
                    });
                } else {
                    return new this.NoResultsViewConstructor({
                        searchQuery: this.searchResults.searchQuery
                    });
                }
            }

            return null;
        },

        getCollection: function () {
            if (this.searchResults) {
                return this.searchResults.collection;
            }

            return null;
        },

        onClose: function () {
            this.searchResults = null;
        },

        onBeforeSearchStart: function () {
            this.searchDeferred = $.Deferred();
            this.searchPromise = this.searchDeferred.promise();
            this.hideErrorMessage();
            this.searchResults = null;
            // If tab doesn't exist, creates it.
            if (!this.tabModel) {
                this.createTab();
            }
            // If tab is not already active, makes it active
            if (!this.tabModel.isActive()) {
                this.tabModel.activate();
            } else {
                this.render();
            }
        },

        onSearch: function (collection, total, searchQuery) {
            this.searchResults = {
                collection: collection,
                total: total,
                searchQuery: searchQuery
            };
            if (this.searchDeferred) {
                this.searchDeferred.resolve();
            }
        },

        onSearchError: function (errorMessage) {
            this.showErrorMessage(errorMessage);
            if (this.searchDeferred) {
                this.searchDeferred.reject();
            }
        }
    });

    return SearchResultsView;
});
}).call(this, define || RequireJS.define);
