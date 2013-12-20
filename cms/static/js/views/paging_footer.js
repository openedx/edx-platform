define(["backbone"], function(Backbone, AssetView) {

    var PagingFooter = Backbone.View.extend({
        initialize: function(options) {
            var view = options.view,
                collection = view.collection;
            this.view = view;
            this.template = _.template($("#paging-footer-tpl").text());
            collection.bind('add', _.bind(this.render, this));
            collection.bind('remove', _.bind(this.render, this));
            collection.bind('reset', _.bind(this.render, this));
            this.render();
        },

        render: function() {
            var view = this.view,
                collection = view.collection,
                currentPage = collection.currentPage,
                lastPage = collection.totalPages - 1;
            this.$el.html(this.template({
                current_page: collection.currentPage,
                total_pages: collection.totalPages
            }));
            $(".previous-page-link").toggleClass("is-disabled", currentPage === 0);
            $(".next-page-link").toggleClass("is-disabled", currentPage === lastPage);
            return this;
        }
    });

    return PagingFooter;
}); // end define();
