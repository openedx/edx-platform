;(function (define) {
    'use strict';
    define(["underscore", "backbone", "gettext"],
        function(_, Backbone, gettext) {

            var PagingView = Backbone.View.extend({
                // takes a Backbone Paginator as a model

                initialize: function() {
                    Backbone.View.prototype.initialize.call(this);
                    var collection = this.collection;
                    collection.bind('add', _.bind(this.onPageRefresh, this));
                    collection.bind('remove', _.bind(this.onPageRefresh, this));
                    collection.bind('reset', _.bind(this.onPageRefresh, this));
                    collection.bind('error', _.bind(this.onError, this));
                    collection.bind('page_changed', function () { window.scrollTo(0, 0); });
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

                registerFilterableColumn: function(columnName, displayName, fieldName) {
                    this.collection.registerFilterableColumn(columnName, displayName, fieldName);
                },

                filterableColumnInfo: function(filterColumn) {
                    return this.collection.filterableColumnInfo(filterColumn);
                },

                filterDisplayName: function() {
                    return this.collection.filterDisplayName();
                },

                setInitialFilterColumn: function(filterColumn) {
                    var collection = this.collection,
                        filterInfo = collection.filterableColumns[filterColumn];
                    collection.filterField = filterInfo.fieldName;
                    collection.filterColumn = filterColumn;
                },

                /**
                * Registers information about a column that can be sorted.
                * @param columnName The element name of the column.
                * @param displayName The display name for the column in the current locale.
                * @param fieldName The database field name that is represented by this column.
                * @param defaultSortDirection The default sort direction for the column
                */
                registerSortableColumn: function(columnName, displayName, fieldName, defaultSortDirection) {
                    this.collection.registerSortableColumn(columnName, displayName, fieldName, defaultSortDirection);
                },

                sortableColumnInfo: function(sortColumn) {
                    return this.collection.sortableColumnInfo(sortColumn);
                },

                sortDisplayName: function() {
                    return this.collection.sortDisplayName();
                },

                setInitialSortColumn: function(sortColumn) {
                    var collection = this.collection,
                        sortInfo = collection.sortableColumnInfo(sortColumn);
                    collection.sortField = sortInfo.fieldName;
                    collection.sortDirection = sortInfo.defaultSortDirection;
                    collection.sortColumn = sortColumn;
                },

                toggleSortOrder: function(sortColumn) {
                    var collection = this.collection,
                        sortInfo = this.collection.sortableColumnInfo(sortColumn),
                        sortField = sortInfo.fieldName,
                        defaultSortDirection = sortInfo.defaultSortDirection;
                    if (collection.sortField === sortField) {
                        collection.sortDirection = collection.sortDirection === 'asc' ? 'desc' : 'asc';
                    } else {
                        collection.sortField = sortField;
                        collection.sortDirection = defaultSortDirection;
                    }
                    collection.sortColumn = sortColumn;
                    this.collection.setPage(0);
                },

                selectFilter: function(filterColumn) {
                    var collection = this.collection,
                        filterInfo = collection.filterableColumnInfo(filterColumn),
                        filterField = filterInfo.fieldName,
                        defaultFilterKey = false;
                    if (collection.filterField !== filterField) {
                        collection.filterField = filterField;
                    }
                    collection.filterColumn = filterColumn;
                    this.collection.setPage(0);
                }
            });
            return PagingView;
        }); // end define();
}).call(this, define || RequireJS.define);
