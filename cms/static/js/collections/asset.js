define(["backbone.paginator", "js/models/asset"], function(BackbonePaginator, AssetModel) {
    var AssetCollection = BackbonePaginator.requestPager.extend({
        sortableColumns: {},
        filterableColumns: {},
        sortColumn: '',
        filterColumn: '',
        assetType: '',
        model : AssetModel,
        paginator_core: {
            type: 'GET',
            accepts: 'application/json',
            dataType: 'json',
            url: function() { return this.url; }
        },
        paginator_ui: {
            firstPage: 0,
            currentPage: 0,
            perPage: 50
        },
        server_api: {
            'page': function() { return this.currentPage; },
            'page_size': function() { return this.perPage; },
            'sort': function() { return this.sortField; },
            'direction': function() { return this.sortDirection; },
            'asset_type': function() { return this.assetType; },
            'format': 'json'
        },

        parse: function(response) {
            var totalCount = response.totalCount,
                start = response.start,
                currentPage = response.page,
                pageSize = response.pageSize,
                totalPages = Math.ceil(totalCount / pageSize);
            this.totalCount = totalCount;
            this.totalPages = Math.max(totalPages, 1); // Treat an empty collection as having 1 page...
            this.currentPage = currentPage;
            this.start = start;
            return response.assets;
        },

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
            });
        },

        nextPage: function () {
            if (this.currentPage < this.totalPages - 1) {
                this.setPage(this.currentPage + 1);
            }
        },

        previousPage: function () {
            if (this.currentPage > 0) {
                this.setPage(this.currentPage - 1);
            }
        },

        registerSortableColumn: function(columnName, displayName, fieldName, defaultSortDirection) {
            this.sortableColumns[columnName] = {
                displayName: displayName,
                fieldName: fieldName,
                defaultSortDirection: defaultSortDirection
            }
        },

        sortableColumnInfo: function (sortColumn) {
            var sortInfo = this.sortableColumns[sortColumn];
            if (!sortInfo) {
                throw "Unregistered filter column '" + filterInfo + "'";
            }
            return sortInfo;
        },

        sortDisplayName: function () {
            return this.sortableColumnInfo(this.sortColumn).displayName;
        },

        registerFilterableColumn: function (columnName, displayName, fieldName) {
            this.filterableColumns[columnName] = {
                displayName: displayName,
                fieldName: fieldName
            };
        },

        filterableColumnInfo: function(filterColumn) {
            var filterInfo = this.filterableColumns[filterColumn];
            if (!filterInfo) {
                throw "Unregistered filter column'" + filterInfo + "'";
            }
            return filterInfo;
        },

        filterDisplayName: function () {
            return this.filterableColumnInfo(this.filterColumn).displayName;
        }
    });
    return AssetCollection;
});
