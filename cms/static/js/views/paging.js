define(["backbone", "js/views/feedback_alert", "gettext"], function(Backbone, AlertView, gettext) {

    var PagingView = Backbone.View.extend({
        // takes a Backbone Paginator as a model

        sortableColumns: {},

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

        setPage: function(page) {
            var self = this,
                collection = self.collection,
                oldPage = collection.currentPage;
            collection.goTo(page, {
                reset: true,
                success: function() {
                    window.scrollTo(0, 0);
                },
                error: function(collection, response, options) {
                    collection.currentPage = oldPage;
                }
            });
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

        registerSortableColumn: function(columnName, displayName, fieldName, sortDirection) {
            this.sortableColumns[columnName] = {
                displayName: displayName,
                fieldName: fieldName,
                sortDirection: sortDirection
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

        setDefaultSortColumn: function(sortColumn) {
            var collection = this.collection,
                sortInfo = this.sortableColumns[sortColumn],
                sortField = sortInfo.fieldName,
                defaultSortDirection = sortInfo.sortDirection;
            collection.sortField = sortField;
            collection.sortDirection = defaultSortDirection;
            this.sortColumn = sortColumn;
        },

        toggleSortOrder: function(sortColumn) {
            var collection = this.collection,
                sortInfo = this.sortableColumnInfo(sortColumn),
                sortField = sortInfo.fieldName,
                defaultSortDirection = sortInfo.sortDirection;
            if (collection.sortField === sortField) {
                collection.sortDirection = collection.sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                collection.sortField = sortField;
                collection.sortDirection = defaultSortDirection;
            }
            this.sortColumn = sortColumn;
            this.setPage(0);
        }
    });

    return PagingView;
}); // end define();
