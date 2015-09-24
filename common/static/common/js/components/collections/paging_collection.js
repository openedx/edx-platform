/**
 * A generic paging collection for use with a ListView and PagingFooter.
 *
 * By default this collection is designed to work with Django Rest Framework APIs, but can be configured to work with
 * others. There is support for ascending or descending sort on a particular field, as well as filtering on a field.
 * While the backend API may use either zero or one indexed page numbers, this collection uniformly exposes a one
 * indexed interface to make consumption easier for views.
 *
 * Subclasses may want to override the following properties:
 *      - url (string): The base url for the API endpoint.
 *      - isZeroIndexed (boolean): If true, API calls will use page numbers starting at zero. Defaults to false.
 *      - perPage (number): Count of elements to fetch for each page.
 *      - server_api (object): Query parameters for the API call. Subclasses may add entries as necessary. By default,
 *          a 'sort_order' field is included to specify the field to sort on. This field may be removed for subclasses
 *          that do not support sort ordering, or support it in a non-standard way. By default filterField and
 *          sortDirection do not affect the API calls. It is up to subclasses to add this information to the appropriate
 *          query string parameters in server_api.
 */
;(function (define) {
    'use strict';
    define(['backbone.paginator'], function (BackbonePaginator) {
        var PagingCollection = BackbonePaginator.requestPager.extend({
            initialize: function () {
                // These must be initialized in the constructor because otherwise all PagingCollections would point
                // to the same object references for sortableFields and filterableFields.
                this.sortableFields = {};
                this.filterableFields = {};
            },

            isZeroIndexed: false,
            perPage: 10,

            isStale: false,

            sortField: '',
            sortDirection: 'descending',
            sortableFields: {},

            filterField: '',
            filterableFields: {},

            searchString: null,

            paginator_core: {
                type: 'GET',
                dataType: 'json',
                url: function () { return this.url; }
            },

            paginator_ui: {
                firstPage: function () { return this.isZeroIndexed ? 0 : 1; },
                // Specifies the initial page during collection initialization
                currentPage: function () { return this.isZeroIndexed ? 0 : 1; },
                perPage: function () { return this.perPage; }
            },

            server_api: {
                page: function () { return this.currentPage; },
                page_size: function () { return this.perPage; },
                text_search: function () { return this.searchString ? this.searchString : ''; },
                sort_order: function () { return this.sortField; }
            },

            parse: function (response) {
                this.totalCount = response.count;
                this.currentPage = response.current_page;
                this.totalPages = response.num_pages;
                this.start = response.start;

                // Note: sort_order is not returned when performing a search
                if (response.sort_order) {
                    this.sortField = response.sort_order;
                }
                return response.results;
            },

            /**
             * Returns the current page number as if numbering starts on page one, regardless of the indexing of the
             * underlying server API.
             */
            getPage: function () {
                return this.currentPage + (this.isZeroIndexed ? 1 : 0);
            },

            /**
             * Sets the current page of the collection. Page is assumed to be one indexed, regardless of the indexing
             * of the underlying server API. If there is an error fetching the page, the Backbone 'error' event is
             * triggered and the page does not change. A 'page_changed' event is triggered on a successful page change.
             * @param page one-indexed page to change to
             */
            setPage: function (page) {
                var oldPage = this.currentPage,
                    self = this,
                    deferred = $.Deferred();
                this.goTo(page - (this.isZeroIndexed ? 1 : 0), {reset: true}).then(
                    function () {
                        self.isStale = false;
                        self.trigger('page_changed');
                        deferred.resolve();
                    },
                    function () {
                        self.currentPage = oldPage;
                        deferred.fail();
                    }
                );
                return deferred.promise();
            },


            /**
             * Refreshes the collection if it has been marked as stale.
             * @returns {promise} Returns a promise representing the refresh.
             */
            refresh: function() {
                var deferred = $.Deferred();
                if (this.isStale) {
                    this.setPage(1)
                        .done(function() {
                            deferred.resolve();
                        });
                } else {
                    deferred.resolve();
                }
                return deferred.promise();
            },

            /**
             * Returns true if the collection has a next page, false otherwise.
             */
            hasNextPage: function () {
                return this.getPage() < this.totalPages;
            },

            /**
             * Returns true if the collection has a previous page, false otherwise.
             */
            hasPreviousPage: function () {
                return this.getPage() > 1;
            },

            /**
             * Moves the collection to the next page if it exists.
             */
            nextPage: function () {
                if (this.hasNextPage()) {
                    this.setPage(this.getPage() + 1);
                }
            },

            /**
             * Moves the collection to the previous page if it exists.
             */
            previousPage: function () {
                if (this.hasPreviousPage()) {
                    this.setPage(this.getPage() - 1);
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
             * Sets the field to sort on. Sends a request to the server to fetch the first page of the collection with
             * the new sort order. If successful, the collection resets to page one with the new data.
             * @param fieldName name of the field to sort on
             * @param toggleDirection if true, the sort direction is toggled if the given field was already set
             */
            setSortField: function (fieldName, toggleDirection) {
                if (toggleDirection) {
                    if (this.sortField === fieldName) {
                        this.sortDirection = PagingCollection.SortDirection.flip(this.sortDirection);
                    } else {
                        this.sortDirection = PagingCollection.SortDirection.DESCENDING;
                    }
                }
                this.sortField = fieldName;
                this.isStale = true;
            },

            /**
             * Sets the direction of the sort. Sends a request to the server to fetch the first page of the collection
             * with the new sort order. If successful, the collection resets to page one with the new data.
             * @param direction either ASCENDING or DESCENDING from PagingCollection.SortDirection.
             */
            setSortDirection: function (direction) {
                this.sortDirection = direction;
                this.isStale = true;
            },

            /**
             * Sets the field to filter on. Sends a request to the server to fetch the first page of the collection
             * with the new filter options. If successful, the collection resets to page one with the new data.
             * @param fieldName name of the field to filter on
             */
            setFilterField: function (fieldName) {
                this.filterField = fieldName;
                this.isStale = true;
            },

            /**
             * Sets the string to use for a text search. If no string is specified then
             * the search is cleared.
             * @param searchString A string to search on, or null if no search is to be applied.
             */
            setSearchString: function(searchString) {
                if (searchString !== this.searchString) {
                    this.searchString = searchString;
                    this.isStale = true;
                }
            }
        }, {
            SortDirection: {
                ASCENDING: 'ascending',
                DESCENDING: 'descending',
                flip: function (direction) {
                    return direction === this.ASCENDING ? this.DESCENDING : this.ASCENDING;
                }
            }
        });
        return PagingCollection;
    });
}).call(this, define || RequireJS.define);
