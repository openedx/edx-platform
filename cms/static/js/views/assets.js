define(["js/views/paging", "js/views/asset", "js/views/paging_header", "js/views/paging_footer"],
    function(PagingView, AssetView, PagingHeader, PagingFooter) {

var AssetsView = PagingView.extend({
    // takes AssetCollection as model

    initialize : function() {
        PagingView.prototype.initialize.call(this);
        var collection = this.collection;
        this.emptyTemplate = _.template($("#no-assets-tpl").text());
        this.template = _.template($("#asset-library-tpl").text());
        this.listenTo(collection, 'destroy', this.handleDestroy);
        this.render();
        this.setPage(0);
    },

    render: function() {
        var self = this;
        self.$el.html(self.template());
        self.tableBody = $('#asset-table-body');
        self.pagingHeader = new PagingHeader({view: self, el: $('#asset-paging-header')});
        self.pagingFooter = new PagingFooter({view: self, el: $('#asset-paging-footer')});
        return this;
    },

    renderPageItems: function() {
        var self = this,
            assets = this.collection,
            hasAssets = assets.length > 0;
        if (hasAssets) {
            self.tableBody.empty();
            assets.each(
                function(asset) {
                    var view = new AssetView({model: asset});
                    self.tableBody.append(view.render().el);
                });
        }
        $('.asset-library').toggle(hasAssets);
        $('.no-asset-content').toggle(!hasAssets);
        return this;
    },

    handleDestroy: function(model, collection, options) {
        this.collection.fetch({reset: true}); // reload the collection to get a fresh page full of items
        analytics.track('Deleted Asset', {
            'course': course_location_analytics,
            'id': model.get('url')
        });
    },

    addAsset: function (model) {
        this.setPage(0);

        analytics.track('Uploaded a File', {
            'course': course_location_analytics,
            'asset_url': model.get('url')
        });
    }
});

return AssetsView;
}); // end define();
