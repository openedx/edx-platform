/**
 * A generic server paging collection.
 *
 * By default this collection is designed to work with Django Rest
 * Framework APIs, but can be configured to work with others. There is
 * support for ascending or descending sort on a particular field, as
 * well as filtering on a field. While the backend API may use either
 * zero or one indexed page numbers, this collection uniformly exposes a
 * one indexed interface to make consumption easier for views.
 *
 * Subclasses may want to override the following properties:
 *
 * - url (`string`): The base URL for the API endpoint.
 * - state (`object`): Object to overrride default state values
 *   provided to `Backbone.paginator`.
 * - queryParams (`object`): Specifies Query parameters for the API
 *   call using the `Backbone.paginator` API.  In the case of built-
 *   in `Backbone.paginator` state keys, this maps those state keys
 *   to query parameter keys.  queryParams can also map query
 *   parameter keys to functions providing values for such keys.
 *   Subclasses may add entries as necessary. By default,
 *   `'sort_order'` is the query parameter used for sorting, with
 *   values of `'asc'` for increasing sort and `'desc'` for decreasing
 *   sort.
 *
 * @module PagingCollection
 */
(function(define) {
    'use strict';

    define(['jquery', 'underscore', 'backbone.paginator'], function($, _, PageableCollection) {
        var PagingCollection = PageableCollection.extend({
            mode: 'server',

            isStale: false,

            sortableFields: {},

            filterableFields: {},

            state: {
                firstPage: 1,
                pageSize: 10,
                sortKey: null
            },

            queryParams: {
                currentPage: 'page',
                pageSize: 'page_size',
                totalRecords: 'count',
                totalPages: 'num_pages',
                sortKey: 'order_by',
                order: 'sort_order'
            },

            constructor: function(models, options) {
                this.state = _.extend({}, PagingCollection.prototype.state, this.state);
                this.queryParams = _.extend({}, PagingCollection.prototype.queryParams, this.queryParams);
                PageableCollection.prototype.constructor.call(this, models, options);
            },

            initialize: function(models, options) {
                // These must be initialized in the constructor
                // because otherwise all PagingCollections would point
                // to the same object references for sortableFields
                // and filterableFields.
                this.sortableFields = {};
                this.filterableFields = {};
                PageableCollection.prototype.initialize.call(this, models, options);
            },

            parse: function(response, options) {
                // PageableCollection expects the response to be an
                // array of two elements - the server-side state
                // metadata (page, size, etc.), and the array of
                // objects.
                var modifiedResponse = [];
                modifiedResponse.push(_.omit(response, 'results'));
                modifiedResponse.push(response.results);
                return PageableCollection.prototype.parse.call(this, modifiedResponse, options);
            },

            /**
             * Returns the current page number as if numbering starts on
             * page one, regardless of the indexing of the underlying
             * server API.
             *
             * @returns {integer} The current page number.
             */
            getPageNumber: function() {
                return this.state.currentPage + (1 - this.state.firstPage);
            },

            /**
             * Returns the total pages of the collection based on
             * total records and page size
             *
             * @returns {integer} Total number of pages.
             */
            getTotalPages: function() {
                return this.state.totalPages;
            },

            /**
             * Returns the total number of records the collection has
             *
             * @returns {integer} Total number of records.
             */
            getTotalRecords: function() {
                return this.state.totalRecords;
            },

            /**
             * Returns the number of records per page
             *
             * @returns {integer} Number of records per page.
             */
            getPageSize: function() {
                return this.state.pageSize;
            },

            /**
             * Sets the current page of the collection. Page is assumed
             * to be one indexed, regardless of the indexing of the
             * underlying server API. If there is an error fetching the
             * page, the Backbone 'error' event is triggered and the
             * page does not change. A 'page_changed' event is triggered
             * on a successful page change.
             *
             * @param page {integer} one-indexed page to change to.
             */
            setPage: function(page) {
                var oldPage = this.state.currentPage,
                    self = this,
                    deferred = $.Deferred();
                this.getPage(page - (1 - this.state.firstPage), {reset: true}).then(
                    function() {
                        self.isStale = false;
                        self.trigger('page_changed');
                        deferred.resolve();
                    },
                    function() {
                        self.state.currentPage = oldPage;
                        deferred.fail();
                    }
                );
                return deferred.promise();
            },

            /**
             * Refreshes the collection if it has been marked as stale.
             *
             * @returns {promise} Returns a promise representing the
             *     refresh.
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
             * Returns true if the collection has a next page, false
             * otherwise.
             *
             * @returns {boolean} Returns true if the collection has a next page.
             */
            hasNextPage: function() {
                return this.getPageNumber() < this.state.totalPages;
            },

            /**
             * Returns true if the collection has a previous page, false
             * otherwise.
             *
             * @returns {boolean} Returns true if the collection has a previous page.
             */
            hasPreviousPage: function() {
                return this.getPageNumber() > 1;
            },

            /**
             * Moves the collection to the next page if it exists.
             */
            nextPage: function() {
                if (this.hasNextPage()) {
                    this.setPage(this.getPageNumber() + 1);
                }
            },

            /**
             * Moves the collection to the previous page if it exists.
             */
            previousPage: function() {
                if (this.hasPreviousPage()) {
                    this.setPage(this.getPageNumber() - 1);
                }
            },

            /**
             * Adds the given field to the list of fields that can be
             * sorted on.
             *
             * @param fieldName {string} name of the field for the server API
             * @param displayName {string} name of the field to display to the
             *     user
             */
            registerSortableField: function(fieldName, displayName) {
                this.addField(this.sortableFields, fieldName, displayName);
            },

            /**
             * Adds the given field to the list of fields that can be
             * filtered on.
             *
             * @param fieldName {string} name of the field for the server API
             * @param displayName {string} name of the field to display to the
             *     user
             */
            registerFilterableField: function(fieldName, displayName) {
                this.addField(this.filterableFields, fieldName, displayName);
            },

            /**
             * For internal use only. Adds the given field to the given
             * collection of fields.
             * @param fields {object} object of existing fields
             * @param fieldName {string} name of the field for the server API
             * @param displayName {string} name of the field to display to the
             *     user
             */
            addField: function(fields, fieldName, displayName) {
                var newField = {};
                newField[fieldName] = {
                    displayName: displayName
                };
                _.extend(fields, newField);
            },

            /**
             * Returns the display name of the field that the collection
             * is currently sorted on.
             *
             * @returns {string} The display name of the sort field.
             */
            sortDisplayName: function() {
                if (this.state.sortKey) {
                    return this.sortableFields[this.state.sortKey].displayName;
                } else {
                    return '';
                }
            },

            /**
             * Returns the display name of a specified filterable field.
             *
             * @param fieldName {string} querystring parameter name for the
             *     filterable field
             * @returns {string} The display name of the specified filterable field.
             */
            filterDisplayName: function(fieldName) {
                if (!_.isUndefined(this.filterableFields[fieldName])) {
                    return this.filterableFields[fieldName].displayName;
                } else {
                    return '';
                }
            },

            /**
             * Sets the field to sort on and marks the collection as
             * stale.
             *
             * @param fieldName {string} name of the field to sort on
             * @param toggleDirection {boolean} if true, the sort direction is
             *     toggled if the given field was already set
             */
            setSortField: function(fieldName, toggleDirection) {
                var direction = toggleDirection ? 0 - this.state.order : this.state.order;
                if (fieldName !== this.state.sortKey || toggleDirection) {
                    this.setSorting(fieldName, direction);
                    this.isStale = true;
                }
            },

            /**
             * Returns the direction of the current sort.
             *
             * The return value is one of the following:
             *
             * - `asc` - indicates that the sort is ascending.
             * - `desc` - indicates that the sort is descending.
             *
             * @returns {string} Returns the direction of the current sort.
             */
            sortDirection: function() {
                return (this.state.order === -1) ?
                    PagingCollection.SortDirection.ASCENDING :
                    PagingCollection.SortDirection.DESCENDING;
            },

            /**
             * Sets the direction of the sort and marks the collection
             * as stale.  Assumes (and requires) that the sort key has
             * already been set.
             *
             * @param direction {string} either ASCENDING or DESCENDING from
             *     PagingCollection.SortDirection.
             */
            setSortDirection: function(direction) {
                var currentOrder = this.state.order,
                    newOrder = currentOrder;
                if (direction === PagingCollection.SortDirection.ASCENDING) {
                    newOrder = -1;
                } else if (direction === PagingCollection.SortDirection.DESCENDING) {
                    newOrder = 1;
                }
                if (newOrder !== currentOrder) {
                    this.setSorting(this.state.sortKey, newOrder);
                    this.isStale = true;
                }
            },

            /**
             * Flips the sort order.
             */
            flipSortDirection: function() {
                this.setSorting(this.state.sortKey, 0 - this.state.order);
                this.isStale = true;
            },

            /**
             * Returns whether this collection has defined a given
             * filterable field.
             *
             * @param fieldName {string} querystring parameter name for the
             *     filterable field
             * @return {boolean} Returns true if this collection has the specified field.
             */
            hasRegisteredFilterField: function(fieldName) {
                return _.has(this.filterableFields, fieldName) &&
                    !_.isUndefined(this.filterableFields[fieldName].displayName);
            },

            /**
             * Returns whether this collection has set a filterable field.
             *
             * @param fieldName {string} querystring parameter name for the
             *     filterable field
             * @return {boolean} Returns true if this collection has set the specified field.
             */
            hasSetFilterField: function(fieldName) {
                return _.has(this.filterableFields, fieldName) && !_.isNull(this.filterableFields[fieldName].value);
            },

            /**
             * Gets an object of currently active (applied) filters.  Excludes
             * the active search by default.
             * @param {bool} includeSearch - Whether search should be included
             * in the result.
             * @returns {Object} An object mapping the names of currently active
             * filter fields to their values.
             */
            getActiveFilterFields: function(includeSearch) {
                var activeFilterFields = _.chain(this.filterableFields)
                    .pick(function(fieldData) {
                        return !_.isNull(fieldData.value) && !_.isUndefined(fieldData.value);
                    })
                    .mapObject(function(data) {
                        return data.value;
                    });
                if (!includeSearch) {
                    activeFilterFields = activeFilterFields.omit(PagingCollection.DefaultSearchKey);
                }
                return activeFilterFields.value();
            },

            /**
             * Gets the value of the given filter field.
             *
             * @returns {String} the current value of the requested filter
             *     field.  null means that the filter field is not active.
             */
            getFilterFieldValue: function(filterFieldName) {
                var val = this.getActiveFilterFields(true)[filterFieldName];
                return (_.isNull(val) || _.isUndefined(val)) ? null : val;
            },

            /**
             * Sets a filter field to a given value and marks the
             * collection as stale.
             *
             * @param fieldName {string} querystring parameter name for the
             *     filterable field
             * @param value {*} value for the filterable field
             */
            setFilterField: function(fieldName, value) {
                var queryStringValue;
                if (!this.hasRegisteredFilterField(fieldName)) {
                    this.registerFilterableField(fieldName, '');
                }
                this.filterableFields[fieldName].value = value;
                if (_.isArray(value)) {
                    queryStringValue = value.join(',');
                } else {
                    queryStringValue = value;
                }
                this.queryParams[fieldName] = function() {
                    return queryStringValue || null;
                };
                this.isStale = true;
            },

            /**
             * Unsets a filterable field and marks the collection as
             * stale.
             *
             * @param fieldName {string} querystring parameter name for the
             *     filterable field
             */
            unsetFilterField: function(fieldName) {
                if (this.hasSetFilterField(fieldName)) {
                    this.setFilterField(fieldName, null);
                }
            },

            /**
             * Unsets all of the collections filterable fields and marks
             * the collection as stale.
             */
            unsetAllFilterFields: function() {
                _.each(_.keys(this.filterableFields), _.bind(this.unsetFilterField, this));
            },

            /**
             * Gets the value of the current search string.
             *
             * @returns {String} the current value of the search string.  null
             * or undefined means that the filter field is not active.
             */
            getSearchString: function() {
                return this.getFilterFieldValue(PagingCollection.DefaultSearchKey);
            },

            /**
             * Tells whether a search is currently applied.
             *
             * @returns {bool} - whether a search is currently applied.
             */
            hasActiveSearch: function() {
                var currentSearch = this.getSearchString();
                return !_.isNull(currentSearch) && currentSearch !== '';
            },

            /**
             * Sets the string to use for a text search and marks the
             * collection as stale.
             *
             * @param searchString {string} A string to search on, or null if no
             *     search is to be applied.
             */
            setSearchString: function(searchString) {
                if (searchString !== this.getSearchString()) {
                    this.setFilterField(PagingCollection.DefaultSearchKey, searchString);
                }
            },

            /**
             * Unsets the string to use for a text search and marks the
             * collection as stale.
             */
            unsetSearchString: function() {
                this.unsetFilterField(PagingCollection.DefaultSearchKey);
            }
        }, {
            DefaultSearchKey: 'text_search',
            SortDirection: {
                ASCENDING: 'asc',
                DESCENDING: 'desc'
            }
        });

        return PagingCollection;
    });
}).call(
    this,
    // Use the default 'define' function if available, else use 'RequireJS.define'
    typeof define === 'function' && define.amd ? define : RequireJS.define
);
