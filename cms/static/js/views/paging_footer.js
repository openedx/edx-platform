define(["backbone", "underscore"], function(Backbone, _) {

    var PagingFooter = Backbone.View.extend({
        events : {
            "click .next-page-link": "nextPage",
            "click .previous-page-link": "previousPage",
            "change .page-number-input": "changePage"
        },

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
            this.$(".previous-page-link").toggleClass("is-disabled", currentPage === 0);
            this.$(".next-page-link").toggleClass("is-disabled", currentPage === lastPage);
            return this;
        },

        changePage: function() {
            var view = this.view,
                collection = view.collection,
                currentPage = collection.currentPage + 1,
                pageInput = this.$("#page-number-input"),
                pageNumber = parseInt(pageInput.val(), 10);
            if (pageNumber && pageNumber !== currentPage) {
                view.setPage(pageNumber - 1);
            }
            pageInput.val(""); // Clear the value as the label will show beneath it
        },

        nextPage: function() {
            this.view.nextPage();
        },

        previousPage: function() {
            this.view.previousPage();
        }
    });

    return PagingFooter;
}); // end define();
