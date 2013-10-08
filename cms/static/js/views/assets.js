define(["backbone", "js/views/asset"], function(Backbone, AssetView) {

var AssetsView = Backbone.View.extend({
    // takes AssetCollection as model

    initialize : function() {
        this.listenTo(this.collection, 'destroy', this.handleDestroy);
        this.render();
    },

    render: function() {
        this.$el.empty();

        var self = this;
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
        // If asset is not already being shown, add it.
        if (this.collection.findWhere({'url': model.get('url')}) === undefined) {
            this.collection.add(model, {at: 0});
            var view = new AssetView({model: model});
            this.$el.prepend(view.render().el);

            analytics.track('Uploaded a File', {
                'course': course_location_analytics,
                'asset_url': model.get('url')
            });
        }
    }
});

return AssetsView;
}); // end define();
