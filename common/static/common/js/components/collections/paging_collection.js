;(function (define) {
    'use strict';
    define(['backbone.paginator'], function (BackbonePaginator) {
        var PagingCollection = BackbonePaginator.requestPager.extend({
            paginator_core: {
                type: 'GET',
                dataType: 'json',
                url: function () { return this.url }
            },

            paginator_ui: {
                firstPage: function () { return this.isZeroIndexed ? 0 : 1; },
                currentPage: function () { return this.isZeroIndexed ? 0 : 1; },
                perPage: function () { return this.perPage }
            },

            server_api: {
                'page': function () { return this.currentPage; },
                'page_size': function () { return this.perPage; }
            },

            parse: function (response) {
                this.totalCount = response.count;
                this.currentPage = response.current_page;
                this.totalPages = response.num_pages;
                this.start = response.start;
                return response.results;
            },

            sortField: '',
            sortDirection: 'desc',
            sortableFields: {},

            filterField: '',
            filterableFields: {},

            /**
             * Returns the current page number as if numbering starts on page one, regardless of the indexing of the
             * underlying server API.
             */
            currentOneIndexPage: function () {
                return this.currentPage + (this.isZeroIndexed ? 1 : 0);
            },

            /**
             * Sets the current page of the collection. Page is assumed to be one indexed, regardless of the indexing
             * of the underlying server API.
             * @param page one-indexed page to change to
             */
            setPage: function (page) {
                var oldPage = this.currentPage,
                    self = this;
                this.goTo(page, {
                    reset: true,
                    success: function () {
                        self.trigger('page_changed');
                    },
                    error: function () {
                        self.currentPage = oldPage;
                    }
                })
            },

            /**
             * Returns true if the collection has a next page, false otherwise.
             */
            hasNextPage: function () {
                return this.currentOneIndexPage() + 1 <= this.totalPages;
            },

            /**
             * Returns true if the collection has a previous page, false otherwise.
             */
            hasPreviousPage: function () {
                return this.currentOneIndexPage() - 1 >= 1;
            },

            /**
             * Moves the collection to the next page, if it exists.
             */
            nextPage: function () {
                if (this.hasNextPage()) {
                    this.setPage(this.currentOneIndexPage() + 1);
                }
            },

            /**
             * Moves the collection to the previous page, if it exists.
             */
            previousPage: function () {
                if (this.hasPreviousPage()) {
                    this.setPage(this.currentOneIndexPage() - 1);
                }
            },

            /**
             * Adds the given field to the list of fields that can be sorted on.
             * @param fieldName name of the field for the server API
             * @param displayName name of the field to display to the user
             */
            registerSortableField: function (fieldName, displayName) {
                this.addField(this.sortableFields, fieldName, displayName);
            },

            /**
             * Adds the given field to the list of fields that can be filtered on.
             * @param fieldName name of the field for the server API
             * @param displayName name of the field to display to the user
             */
            registerFilterableField: function (fieldName, displayName) {
                this.addField(this.filterableFields, fieldName, displayName);
            },

            /**
             * For internal use only. Adds the given field to the given collection of fields.
             * @param fields object of existing fields
             * @param fieldName name of the field for the server API
             * @param displayName name of the field to display to the user
             */
            addField: function (fields, fieldName, displayName) {
                fields[fieldName] = {
                    displayName: displayName
                };
            },

            /**
             * Returns the display name of the field that the collection is currently sorted on.
             */
            sortDisplayName: function () {
                return this.sortableFields[this.sortField].displayName;
            },

            /**
             * Returns the display name of the field that the collection is currently filtered on.
             */
            filterDisplayName: function () {
                return this.filterableFields[this.filterField].displayName;
            },

            /**
             * Sets the field to sort on.
             * @param fieldName name of the field to sort on
             */
            setSortField: function (fieldName) {
                this.sortField = fieldName;
                this.setPage(1);
            },

            /**
             * Sets the field to filter on.
             * @param fieldName name of the field to filter on
             */
            setFilterField: function (fieldName) {
                this.filterField = fieldName;
                this.setPage(1);
            }
        });
        return PagingCollection;
    });
}).call(this, define || RequireJS.define);