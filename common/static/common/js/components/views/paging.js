;(function (define) {
    'use strict';
    define(["underscore", "backbone", "gettext", "common/js/components/views/paging_mixin"],
        function(_, Backbone, gettext, PagingMixin) {

            var PagingView = Backbone.View.extend(PagingMixin).extend({
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
                },

                onPageRefresh: function() {
                    var sortColumn = this.sortColumn;
                    this.renderPageItems();
                    this.$('.column-sort-link').removeClass('current-sort');
                    this.$('#' + sortColumn).addClass('current-sort');
                },

                onError: function() {
                    // Do nothing by default
                },

                nextPage: function() {
                    var collection = this.collection,
                        currentPage = collection.currentPage,
                        lastPage = collection.totalPages - 1;
                    if (currentPage < lastPage) {
                        this.setPage(currentPage + 1);
                    }
                },

                previousPage: function() {
                    var collection = this.collection,
                        currentPage = collection.currentPage;
                    if (currentPage > 0) {
                        this.setPage(currentPage - 1);
                    }
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
                        filtertInfo = this.filterableColumns[filterColumn];
                    collection.filterField = filtertInfo.fieldName;
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
                    this.sortColumn = sortColumn;
                    this.setPage(0);
                },

                selectFilter: function(filterColumn) {
                    var collection = this.collection,
                        filterInfo = this.filterableColumnInfo(filterColumn),
                        filterField = filterInfo.fieldName,
                        defaultFilterKey = false;
                    if (collection.filterField !== filterField) {
                        collection.filterField = filterField;
                    }
                    this.filterColumn = filterColumn;
                    this.setPage(0);
                }
            });
            return PagingView;
        }); // end define();
}).call(this, define || RequireJS.define);
