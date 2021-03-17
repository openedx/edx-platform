(function(define, undefined) {
    'use strict';
    define([
        'jquery', 'underscore', 'gettext', 'js/edxnotes/views/tab_panel', 'js/edxnotes/views/tab_view',
        'js/edxnotes/views/search_box', 'edx-ui-toolkit/js/utils/html-utils', 'edx-ui-toolkit/js/utils/string-utils'
    ], function($, _, gettext, TabPanelView, TabView, SearchBoxView, HtmlUtils, StringUtils) {
        var view = 'Search Results';
        var SearchResultsView = TabView.extend({
            PanelConstructor: TabPanelView.extend({
                id: 'search-results-panel',
                title: view,
                className: function() {
                    return [
                        TabPanelView.prototype.className,
                        'note-group'
                    ].join(' ');
                },
                renderContent: function() {
                    this.$el.append(HtmlUtils.HTML(this.getNotes(this.collection.toArray())).toString());
                    return this;
                }
            }),

            NoResultsViewConstructor: TabPanelView.extend({
                id: 'no-results-panel',
                title: 'No results found',
                className: function() {
                    return [
                        TabPanelView.prototype.className,
                        'note-group'
                    ].join(' ');
                },
                renderContent: function() {
                    var message = gettext('No results found for "{query_string}". Please try searching again.');

                    this.$el.append($('<p />', {
                        text: StringUtils.interpolate(message, {
                            query_string: this.options.searchQuery
                        }, true)
                    }));

                    return this;
                }
            }),

            tabInfo: {
                identifier: 'view-search-results',
                name: gettext('Search Results'),
                icon: 'fa fa-search',
                is_closable: true,
                view: view
            },

            initialize: function(options) {
                this.options = _.extend({}, options);
                _.bindAll(this, 'onBeforeSearchStart', 'onSearch', 'onSearchError');
                TabView.prototype.initialize.call(this, options);
                this.searchResults = null;
                this.searchBox = new SearchBoxView({
                    el: document.getElementById('search-notes-form'),
                    debug: this.options.debug,
                    perPage: this.options.perPage,
                    beforeSearchStart: this.onBeforeSearchStart,
                    search: this.onSearch,
                    error: this.onSearchError
                });
            },

            renderContent: function() {
                this.getLoadingIndicator().focus();
                return this.searchPromise.done(_.bind(function() {
                    this.contentView = this.getSubView();
                    if (this.contentView) {
                        this.$('.wrapper-tabs').append(this.contentView.render().$el);
                    }
                }, this));
            },

            getSubView: function() {
                var collection = this.getCollection();
                if (collection) {
                    if (collection.length) {
                        return new this.PanelConstructor({
                            collection: collection,
                            searchQuery: this.searchResults.searchQuery,
                            scrollToTag: this.options.scrollToTag,
                            createHeaderFooter: this.options.createHeaderFooter
                        });
                    } else {
                        return new this.NoResultsViewConstructor({
                            searchQuery: this.searchResults.searchQuery
                        });
                    }
                }

                return null;
            },

            getCollection: function() {
                if (this.searchResults) {
                    return this.searchResults.collection;
                }

                return null;
            },

            onClose: function() {
                this.searchResults = null;
                this.searchBox.clearInput();
            },

            onBeforeSearchStart: function() {
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

            onSearch: function(collection, searchQuery) {
                this.searchResults = {
                    collection: collection,
                    searchQuery: searchQuery
                };

                if (this.searchDeferred) {
                    this.searchDeferred.resolve();
                }

                if (this.contentView) {
                    this.contentView.$el.focus();
                }
            },

            onSearchError: function(errorMessage) {
                this.showErrorMessageHtml(errorMessage);
                if (this.searchDeferred) {
                    this.searchDeferred.reject();
                }
            }
        });

        return SearchResultsView;
    });
}).call(this, define || RequireJS.define);
