(function(define) {
    'use strict';
    define(['underscore', 'backbone', 'gettext'],
        function(_, Backbone, gettext) {
            var PagingView = Backbone.View.extend({
                // takes a Backbone Paginator as a model

                sortableColumns: {},

                filterableColumns: {},

                filterColumn: '',

                initialize: function() {
                    Backbone.View.prototype.initialize.call(this);
                    var collection = this.collection;
                    collection.bind('add', _.bind(this.onPageRefresh, this));
                    collection.bind('remove', _.bind(this.onPageRefresh, this));
                    collection.bind('reset', _.bind(this.onPageRefresh, this));
                    collection.bind('error', _.bind(this.onError, this));
                    collection.bind('page_changed', function() { window.scrollTo(0, 0); });
                },

                onPageRefresh: function() {
                    var sortColumn = this.collection.sortColumn;
                    this.renderPageItems();
                    this.$('.column-sort-link').removeClass('current-sort');
                    this.$('#' + sortColumn).addClass('current-sort');
                },

                onError: function() {
                    // Do nothing by default
                },

                setPage: function(page) {
                    this.collection.setPage(page);
                },

                nextPage: function() {
                    this.collection.nextPage();
                },

                previousPage: function() {
                    this.collection.previousPage();
                },

                registerFilterableColumn: function(columnName, displayName, fieldName) {
                    this.filterableColumns[columnName] = {
                        displayName: displayName,
                        fieldName: fieldName
                    };
                },

                filterableColumnInfo: function(filterColumn) {
                    var filterInfo = this.filterableColumns[filterColumn];
                    if (!filterInfo) {
                        throw "Unregistered filter column '" + filterInfo + '"';
                    }
                    return filterInfo;
                },


                filterDisplayName: function() {
                    var filterColumn = this.filterColumn,
                        filterInfo = this.filterableColumnInfo(filterColumn);
                    return filterInfo.displayName;
                },

                setInitialFilterColumn: function(filterColumn) {
                    var collection = this.collection,
                        filterInfo = this.filterableColumns[filterColumn];
                    collection.filterField = filterInfo.fieldName;
                    this.filterColumn = filterColumn;
                },

                /**
                * Registers information about a column that can be sorted.
                * @param columnName The element name of the column.
                * @param displayName The display name for the column in the current locale.
                * @param fieldName The database field name that is represented by this column.
                * @param defaultSortDirection The default sort direction for the column
                */
                registerSortableColumn: function(columnName, displayName, fieldName, defaultSortDirection) {
                    this.sortableColumns[columnName] = {
                        displayName: displayName,
                        fieldName: fieldName,
                        defaultSortDirection: defaultSortDirection
                    };
                },

                sortableColumnInfo: function(sortColumn) {
                    var sortInfo = this.sortableColumns[sortColumn];
                    if (!sortInfo) {
                        throw "Unregistered sort column '" + sortColumn + '"';
                    }
                    return sortInfo;
                },

                sortDisplayName: function() {
                    var sortColumn = this.sortColumn,
                        sortInfo = this.sortableColumnInfo(sortColumn);
                    return sortInfo.displayName;
                },

                setInitialSortColumn: function(sortColumn) {
                    var collection = this.collection,
                        sortInfo = this.sortableColumns[sortColumn];
                    collection.sortField = sortInfo.fieldName;
                    collection.sortDirection = sortInfo.defaultSortDirection;
                    this.sortColumn = sortColumn;
                },

                toggleSortOrder: function(sortColumn) {
                    var collection = this.collection,
                        sortInfo = this.sortableColumnInfo(sortColumn),
                        sortField = sortInfo.fieldName,
                        defaultSortDirection = sortInfo.defaultSortDirection;

                    if (collection.sortField === sortField) {
                        collection.sortDirection = collection.sortDirection === 'asc' ? 'desc' : 'asc';
                    } else {
                        collection.sortField = sortField;
                        collection.sortDirection = defaultSortDirection;
                    }

                    collection.setSorting(sortField, collection.sortDirection);
                    this.sortColumn = sortColumn;
                    this.collection.setPage(1);
                },

                selectFilter: function(filterColumn) {
                    var collection = this.collection,
                        filterInfo = this.filterableColumnInfo(filterColumn),
                        filterField = filterInfo.fieldName;

                    if (collection.filterField !== filterField) {
                        collection.filterField = filterField;
                    }
                    this.filterColumn = filterColumn;
                    this.collection.setPage(1);
                }
            });
            return PagingView;
        }); // end define();
}).call(this, define || RequireJS.define);
