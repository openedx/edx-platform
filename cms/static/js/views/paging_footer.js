define(["backbone"], function(Backbone, AssetView) {

    var PagingFooter = Backbone.View.extend({
        initialize: function(arguments) {
            var view = arguments.view,
                collection = view.collection;
            this.view = view;
            this.template = _.template($("#paging-footer-tpl").text());
            collection.bind('add', _.bind(this.render, this));
            collection.bind('remove', _.bind(this.render, this));
            collection.bind('reset', _.bind(this.render, this));
        },

        render: function() {
            var view = this.view,
                collection = view.collection;
            this.$el.html(this.template({
                current_page: collection.currentPage,
                total_pages: collection.totalPages
            }));
            return this;
        }
    });

    return PagingFooter;
}); // end define();
