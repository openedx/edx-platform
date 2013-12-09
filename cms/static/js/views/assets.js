define(["backbone", "js/views/paging", "js/views/asset", "js/views/paging_header", "js/views/paging_footer"],
    function(Backbone, PagingView, AssetView, PagingHeader, PagingFooter) {

var AssetsView = PagingView.extend({
    // takes AssetCollection as model

    initialize : function() {
        PagingView.prototype.initialize.call(this);
        var collection = this.collection;
        this.template = _.template($("#asset-library-tpl").text());
        this.render();
        this.listenTo(collection, 'destroy', this.handleDestroy);
    },

    render: function() {
        var self = this;
        self.$el.html(self.template());
        self.tableBody = $('#asset-table-body');
        new PagingHeader({view: self, el: $('#asset-paging-header')});
        new PagingFooter({view: self, el: $('#asset-paging-footer')});
        return this;
    },

    renderPageItems: function() {
        var self = this;
        self.tableBody.empty();
        this.collection.each(
            function(asset) {
                var view = new AssetView({model: asset});
                self.tableBody.append(view.render().el);
            });
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
