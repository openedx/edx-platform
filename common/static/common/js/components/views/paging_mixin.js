;(function (define) {
    'use strict';
    define([],
        function () {
            var PagedMixin = {
                setPage: function (page) {
                    var self = this,
                        collection = self.collection,
                        oldPage = collection.currentPage;
                    collection.goTo(page, {
                        reset: true,
                        success: function () {
                            window.scrollTo(0, 0);
                        },
                        error: function (collection) {
                            collection.currentPage = oldPage;
                            self.onError();
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
            };
            return PagedMixin;
        });
}).call(this, define || RequireJS.define);
