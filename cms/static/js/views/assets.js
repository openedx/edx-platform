define(["js/views/baseview", "js/views/asset"], function(BaseView, AssetView) {

var AssetsView = BaseView.extend({
    // takes AssetCollection as model

    initialize : function() {
        this.listenTo(this.collection, 'destroy', this.handleDestroy);
    },

    render: function() {
        var self = this;
        self.$el.empty();
        this.collection.each(
            function(asset) {
                var view = new AssetView({model: asset});
                self.$el.append(view.render().el);
            });

        return this;
    },

    handleDestroy: function(model, collection, options) {
        var index = options.index;
        this.$el.children().eq(index).remove();

        analytics.track('Deleted Asset', {
            'course': course_location_analytics,
            'id': model.get('url')
        });
    },

    addAsset: function (model) {
        this.refreshAssets();

        analytics.track('Uploaded a File', {
            'course': course_location_analytics,
            'asset_url': model.get('url')
        });
    },

    setPage: function(page) {
        var self = this;
        this.collection.goTo(page, {
            success: function(collection, response) {
                self.render();
            },
            error: function(collection, response, options) {
                window.alert("Error: " + response);
            }
        });
    }
});

return AssetsView;
}); // end define();
