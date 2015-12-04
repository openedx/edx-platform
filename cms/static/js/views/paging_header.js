define(["underscore", "backbone", "gettext", "text!templates/paging-header.underscore"],
    function(_, Backbone, gettext, paging_header_template) {

        var PagingHeader = Backbone.View.extend({
            events : {
                "click .next-page-link": "nextPage",
                "click .previous-page-link": "previousPage"
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
                    currentPage = collection.currentPage,
                    lastPage = collection.totalPages - 1,
                    messageHtml = this.messageHtml();
                this.$el.html(_.template(paging_header_template, {
                    messageHtml: messageHtml
                }));
                this.$(".previous-page-link").toggleClass("is-disabled", currentPage === 0).attr('aria-disabled', currentPage === 0);
                this.$(".next-page-link").toggleClass("is-disabled", currentPage === lastPage).attr('aria-disabled', currentPage === lastPage);
                return this;
            },

            messageHtml: function() {
                var message = '';
                var asset_type = false;
                if (this.view.collection.assetType) {
                    if (this.view.collection.sortDirection === 'asc') {
                        // Translators: sample result:
                        // "Showing 0-9 out of 25 total, filtered by Images, sorted by Date Added ascending"
                        message = gettext('Showing %(current_item_range)s out of %(total_items_count)s, filtered by %(asset_type)s, sorted by %(sort_name)s ascending');
                    } else {
                        // Translators: sample result:
                        // "Showing 0-9 out of 25 total, filtered by Images, sorted by Date Added descending"
                        message = gettext('Showing %(current_item_range)s out of %(total_items_count)s, filtered by %(asset_type)s, sorted by %(sort_name)s descending');
                    }
                    asset_type = this.filterNameLabel();
                }
                else {
                    if (this.view.collection.sortDirection === 'asc') {
                        // Translators: sample result:
                        // "Showing 0-9 out of 25 total, sorted by Date Added ascending"
                        message = gettext('Showing %(current_item_range)s out of %(total_items_count)s, sorted by %(sort_name)s ascending');
                    } else {
                        // Translators: sample result:
                        // "Showing 0-9 out of 25 total, sorted by Date Added descending"
                        message = gettext('Showing %(current_item_range)s out of %(total_items_count)s, sorted by %(sort_name)s descending');
                    }
                }

                return '<p>' + interpolate(message, {
                        current_item_range: this.currentItemRangeLabel(),
                        total_items_count: this.totalItemsCountLabel(),
                        asset_type: asset_type,
                        sort_name: this.sortNameLabel()
                    }, true) + "</p>";
            },

            currentItemRangeLabel: function() {
                var view = this.view,
                    collection = view.collection,
                    start = collection.start,
                    count = collection.size(),
                    end = start + count;
                return interpolate('<span class="count-current-shown">%(start)s-%(end)s</span>', {
                    start: Math.min(start + 1, end),
                    end: end
                }, true);
            },

            totalItemsCountLabel: function() {
                var totalItemsLabel;
                // Translators: turns into "25 total" to be used in other sentences, e.g. "Showing 0-9 out of 25 total".
                totalItemsLabel = interpolate(gettext('%(total_items)s total'), {
                    total_items: this.view.collection.totalCount
                }, true);
                return interpolate('<span class="count-total">%(total_items_label)s</span>', {
                    total_items_label: totalItemsLabel
                }, true);
            },

            sortNameLabel: function() {
                return interpolate('<span class="sort-order">%(sort_name)s</span>', {
                    sort_name: this.view.sortDisplayName()
                }, true);
            },

            filterNameLabel: function() {
                return interpolate('<span class="filter-column">%(filter_name)s</span>', {
                    filter_name: this.view.filterDisplayName()
                }, true);
            },

            nextPage: function() {
                this.view.nextPage();
            },

            previousPage: function() {
                this.view.previousPage();
            }
        });

        return PagingHeader;
    }); // end define();
