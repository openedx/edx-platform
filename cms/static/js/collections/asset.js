define(["backbone", "backbone.paginator", "js/models/asset"], function(Backbone, BackbonePaginator, AssetModel) {
    var AssetCollection = Backbone.Paginator.requestPager.extend({
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
            perPage: 5
        },
        server_api: {
            'page': function() { return this.currentPage },
            'max': function() { return this.perPage },
            'format': 'json'  // TODO determine how to pass 'accepts' through...
        },

        parse: function(response) {
            var totalCount = response.totalCount,
                start = response.start,
                currentPage = response.page,
                totalPages = Math.ceil(totalCount / this.perPage);
            this.totalCount = totalCount;
            this.totalPages = totalPages;
            this.currentPage = currentPage;
            this.start = start;
            return response.assets;
        }
    });
    return AssetCollection;
});
