define(["backbone.paginator", "js/models/asset", "gettext"], function(BackbonePaginator, AssetModel, gettext) {
    var AssetCollection = BackbonePaginator.requestPager.extend({
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
            'format': 'json'
        },
        sortField: 'displayname', // 'uploadDate',
        sortDirection: 'desc',

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

        sortDisplayName: function() {
            var sortField = this.sortField;
            if (sortField === 'uploadDate') {
                return gettext('Date Added');
            } else if (sortField === 'displayname') {
                return gettext('Name');
            }
        }
    });
    return AssetCollection;
});
