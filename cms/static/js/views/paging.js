define(["backbone", "js/views/feedback_alert"], function(Backbone, AlertView) {

    var PagingView = Backbone.View.extend({
        // takes a Backbone Paginator as a model

        events : {
            "click .next-page-link": "nextPage",
            "click .previous-page-link": "previousPage",
            "change .page-number-input": "changePage"
        },

        initialize: function() {
            Backbone.View.prototype.initialize.call(this);
            var assets = this.collection;
            assets.bind('add', _.bind(this.onRefresh, this));
            assets.bind('remove', _.bind(this.onRefresh, this));
            assets.bind('reset', _.bind(this.onRefresh, this));
        },

        onRefresh: function() {
            var assets = this.collection,
                currentPage = assets.currentPage,
                lastPage = assets.totalPages - 1;
            this.renderPageItems();
            $(".previous-page-link").toggleClass("is-disabled", currentPage == 0)
            $(".next-page-link").toggleClass("is-disabled", currentPage == lastPage)
        },

        changePage: function() {
            var assets = this.collection,
                currentPage = assets.currentPage + 1,
                pageNumber = parseInt(this.$("#page-number-input").val());
            if (pageNumber && pageNumber !== currentPage) {
                this.setPage(pageNumber - 1);
            } else if (!pageNumber) {
                // Remove the invalid page number so that the current page number shows through
                $("#page-number-input").val("")
            }
        },

        setPage: function(page) {
            var self = this,
                assets = self.collection;
            assets.goTo(page, {
                reset: true,
                success: function() {
                    window.scrollTo(0, 0);
                },
                error: function(collection, response, options) {
                    self.showPagingError(response);
                }
            });
        },

        nextPage: function() {
            var assets = this.collection,
                currentPage = assets.currentPage,
                lastPage = assets.totalPages - 1;
            if (currentPage < lastPage) {
                this.setPage(currentPage + 1);
            }
        },

        previousPage: function() {
            var assets = this.collection,
                currentPage = assets.currentPage;
            if (currentPage > 0) {
                this.setPage(currentPage - 1);
            }
        },

        showPagingError: function(response) {
            AlertView.Error({
                title: gettext("Unexpected Error"),
                closeIcon: false
            });
        }
    });

    return PagingView;
}); // end define();
