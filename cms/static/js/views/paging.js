define(["backbone"], function(Backbone, AssetView) {

    var PagingView = Backbone.View.extend({
        // takes a Backbone Paginator as a model

        events : {
            "click .next-page-link": "nextPage",
            "click .previous-page-link": "previousPage",
            "change .page-number-input": "changePage"
        },

        initialize : function() {
            Backbone.View.prototype.initialize.call(this);
            var collection = this.collection;
            collection.bind('add', _.bind(this.renderPageItems, this));
            collection.bind('remove', _.bind(this.renderPageItems, this));
            collection.bind('reset', _.bind(this.renderPageItems, this));
        },

        changePage: function() {
            var pageNumber = parseInt(this.$("#page-number-input").val());
            if (pageNumber) {
                this.setPage(pageNumber - 1);
            }
        },

        setPage: function(page) {
            var self = this;
            this.collection.goTo(page, {
                error: function(collection, response, options) {
                    self.showPagingError(response);
                }
            });
        },

        nextPage: function() {
            var self = this,
                collection = self.collection;
            collection.nextPage({
                error: function(collection, response, options) {
                    self.showPagingError(response);
                }
            });
        },

        previousPage: function() {
            var self = this,
                collection = self.collection;
            collection.prevPage({
                error: function(collection, response, options) {
                    self.showPagingError(response);
                }
            });
        },

        showPagingError: function(response) {
            // TODO how should errors really be shown (andya)
            window.alert("Error: " + response);
        }
    });

    return PagingView;
}); // end define();
