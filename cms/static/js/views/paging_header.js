define([
    'underscore',
    'backbone',
    'gettext',
    'edx-ui-toolkit/js/utils/html-utils',
    'edx-ui-toolkit/js/utils/string-utils',
    'text!templates/paging-header.underscore'
], function(_, Backbone, gettext, HtmlUtils, StringUtils, pagingHeaderTemplate) {
        'use strict';
        /* jshint maxlen:false */
        var PagingHeader = Backbone.View.extend({
            events : {
                'click .next-page-link': 'nextPage',
                'click .previous-page-link': 'previousPage'
            },

            initialize: function(options) {
                var view = options.view,
                    collection = view.collection;
                this.view = view;
                collection.bind('add', _.bind(this.render, this));
                collection.bind('remove', _.bind(this.render, this));
                collection.bind('reset', _.bind(this.render, this));
            },

            render: function() {
                var view = this.view,
                    collection = view.collection,
                    currentPage = collection.getPageNumber(),
                    lastPage = collection.getTotalPages(),
                    messageHtml = this.messageHtml(),
                    isNextDisabled = lastPage === 0 || currentPage === lastPage;
                
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(pagingHeaderTemplate)({messageHtml: messageHtml}));
                this.$('.previous-page-link')
                    .toggleClass('is-disabled', currentPage === 1)
                    .attr('aria-disabled', currentPage === 1);
                this.$('.next-page-link')
                    .toggleClass('is-disabled', isNextDisabled)
                    .attr('aria-disabled', isNextDisabled);

                return this;
            },

            messageHtml: function() {
                var message = '',
                    assetType = false;

                if (this.view.collection.assetType) {
                    if (this.view.collection.sortDirection === 'asc') {
                        // Translators: sample result:
                        // "Showing 0-9 out of 25 total, filtered by Images, sorted by Date Added ascending"
                        message = gettext('Showing {currentItemRange} out of {totalItemsCount}, filtered by {assetType}, sorted by {sortName} ascending');
                    } else {
                        // Translators: sample result:
                        // "Showing 0-9 out of 25 total, filtered by Images, sorted by Date Added descending"
                        message = gettext('Showing {currentItemRange} out of {totalItemsCount}, filtered by {assetType}, sorted by {sortName} descending');
                    }
                    assetType = this.filterNameLabel();
                } else {
                    if (this.view.collection.sortDirection === 'asc') {
                        // Translators: sample result:
                        // "Showing 0-9 out of 25 total, sorted by Date Added ascending"
                        message = gettext('Showing {currentItemRange} out of {totalItemsCount}, sorted by {sortName} ascending');
                    } else {
                        // Translators: sample result:
                        // "Showing 0-9 out of 25 total, sorted by Date Added descending"
                        message = gettext('Showing {currentItemRange} out of {totalItemsCount}, sorted by {sortName} descending');
                    }
                }

                return HtmlUtils.interpolateHtml(message, {
                    currentItemRange: this.currentItemRangeLabel(),
                    totalItemsCount: this.totalItemsCountLabel(),
                    assetType: assetType,
                    sortName: this.sortNameLabel()
                });
            },

            currentItemRangeLabel: function() {
                var view = this.view,
                    collection = view.collection,
                    start = (collection.getPageNumber() - 1) * collection.getPageSize(),
                    count = collection.size(),
                    end = start + count,
                    htmlMessage = HtmlUtils.HTML('<span class="count-current-shown">{start}-{end}</span>');

                return HtmlUtils.interpolateHtml(htmlMessage, {
                    start: Math.min(start + 1, end),
                    end: end
                });
            },

            totalItemsCountLabel: function() {
                var totalItemsLabel,
                    htmlMessage = HtmlUtils.HTML('<span class="count-total">{totalItemsLabel}</span>');

                // Translators: turns into "25 total" to be used in other sentences, e.g. "Showing 0-9 out of 25 total".
                totalItemsLabel = StringUtils.interpolate(gettext('{totalItems} total'), {
                    totalItems: this.view.collection.getTotalRecords()
                });

                return HtmlUtils.interpolateHtml(htmlMessage, {
                    totalItemsLabel: totalItemsLabel
                });
            },

            sortNameLabel: function() {
                var htmlMessage = HtmlUtils.HTML('<span class="sort-order">{sortName}</span>');

                return HtmlUtils.interpolateHtml(htmlMessage, {
                    sortName: this.view.sortDisplayName()
                });
            },

            filterNameLabel: function() {
                var htmlMessage = HtmlUtils.HTML('<span class="filter-column">{filterName}</span>');

                return HtmlUtils.interpolateHtml(htmlMessage, {
                    filterName: this.view.filterDisplayName()
                });
            },

            nextPage: function() {
                this.view.nextPage();
            },

            previousPage: function() {
                this.view.previousPage();
            }
        });

        return PagingHeader;
    });
