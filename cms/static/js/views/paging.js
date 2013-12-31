define(["backbone", "js/views/feedback_alert", "gettext"], function(Backbone, AlertView, gettext) {

    var PagingView = Backbone.View.extend({
        // takes a Backbone Paginator as a model

        initialize: function() {
            Backbone.View.prototype.initialize.call(this);
            var collection = this.collection;
            collection.bind('add', _.bind(this.renderPageItems, this));
            collection.bind('remove', _.bind(this.renderPageItems, this));
            collection.bind('reset', _.bind(this.renderPageItems, this));
        },

        setPage: function(page) {
            var self = this,
                collection = self.collection,
                oldPage = collection.currentPage;
            collection.goTo(page, {
                reset: true,
                success: function() {
                    window.scrollTo(0, 0);
                },
                error: function(collection, response, options) {
                    collection.currentPage = oldPage;
                }
            });
        },

        nextPage: function() {
            var collection = this.collection,
                currentPage = collection.currentPage,
                lastPage = collection.totalPages - 1;
            if (currentPage < lastPage) {
                this.setPage(currentPage + 1);
            }
        },

        previousPage: function() {
            var collection = this.collection,
                currentPage = collection.currentPage;
            if (currentPage > 0) {
                this.setPage(currentPage - 1);
            }
        }
    });

    return PagingView;
}); // end define();
