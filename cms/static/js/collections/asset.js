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
            'start': function() { return this.currentPage },
            'max': function() { return this.perPage },
            'format': 'json'  // TODO determine how to pass 'accepts' through...
        },

        parse: function(response) {
            this.totalPages = Math.ceil(response.totalCount / this.perPage);
            return response.assets;
        }
    });
    return AssetCollection;
});
