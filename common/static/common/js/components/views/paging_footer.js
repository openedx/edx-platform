;(function (define) {
    'use strict';
    define(["underscore", "backbone", "text!common/templates/components/paging-footer.underscore"],
        function(_, Backbone, paging_footer_template) {

            var PagingFooter = Backbone.View.extend({
                events : {
                    "click .next-page-link": "nextPage",
                    "click .previous-page-link": "previousPage",
                    "change .page-number-input": "changePage"
                },

                initialize: function(options) {
                    this.collection = options.collection;
                    this.collection.bind('add', _.bind(this.render, this));
                    this.collection.bind('remove', _.bind(this.render, this));
                    this.collection.bind('reset', _.bind(this.render, this));
                    this.render();
                },

                render: function() {
                    var collection = this.collection,
                        currentPage = collection.currentPage,
                        lastPage = collection.totalPages - 1;
                    this.$el.html(_.template(paging_footer_template, {
                        current_page: collection.currentPage,
                        total_pages: collection.totalPages
                    }));
                    var onFirstPage = !this.collection.hasPreviousPage();
                    var onLastPage = !this.collection.hasNextPage();
                    this.$(".previous-page-link").toggleClass("is-disabled", onFirstPage).attr('aria-disabled', onFirstPage);
                    this.$(".next-page-link").toggleClass("is-disabled", onLastPage).attr('aria-disabled', onLastPage);
                    return this;
                },

                changePage: function() {
                    var collection = this.collection,
                        currentPage = collection.currentPage,
                        pageInput = this.$("#page-number-input"),
                        pageNumber = parseInt(pageInput.val(), 10),
                        validInput = true;
                    if (!pageNumber || pageNumber > collection.totalPages || pageNumber < 1) {
                        validInput = false;
                    }
                    // If we still have a page number by this point,
                    // and it's not the current page, load it.
                    if (validInput && pageNumber !== currentPage) {
                        collection.setPage(pageNumber);
                    }
                    pageInput.val(''); // Clear the value as the label will show beneath it
                },

                nextPage: function() {
                    this.collection.nextPage();
                },

                previousPage: function() {
                    this.collection.previousPage();
                }
            });

            return PagingFooter;
        }); // end define();
}).call(this, define || RequireJS.define);
