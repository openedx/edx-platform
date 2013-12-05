define(["js/views/paging", "js/views/asset", "js/views/paging_header", "js/views/paging_footer"],
    function(PagingView, AssetView, PagingHeader, PagingFooter) {

var AssetsView = PagingView.extend({
    // takes AssetCollection as model

    initialize : function() {
        PagingView.prototype.initialize.call(this);
        var collection = this.collection;
        this.template = _.template($("#asset-library-tpl").text());
        this.listenTo(collection, 'destroy', this.handleDestroy);
    },

    render: function() {
        this.$el.html(this.template());
        this.tableBody = this.$('#asset-table-body');
        this.pagingHeader = new PagingHeader({view: this, el: $('#asset-paging-header')});
        this.pagingFooter = new PagingFooter({view: this, el: $('#asset-paging-footer')});
        this.pagingHeader.render();
        this.pagingFooter.render();

        // Hide the contents until the collection has loaded the first time
        this.$('.asset-library').hide();
        this.$('.no-asset-content').hide();

        return this;
    },

    renderPageItems: function() {
        var self = this,
            assets = this.collection,
            hasAssets = assets.length > 0;
        self.tableBody.empty();
        if (hasAssets) {
            assets.each(
                function(asset) {
                    var view = new AssetView({model: asset});
                    self.tableBody.append(view.render().el);
                });
        }
        self.$('.asset-library').toggle(hasAssets);
        self.$('.no-asset-content').toggle(!hasAssets);
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
