;(function (define) {
    'use strict';
    define(['backbone.paginator'], function (BackbonePaginator) {
        var PagingCollection = BackbonePaginator.requestPager.extend({
            paginator_core: {
                type: 'GET',
                accepts: 'application/json',
                dataType: 'json',
                url: function () { return this.url }
            },

            setPage: function (page) {
                var oldPage = this.currentPage,
                    self = this;
                this.goTo(page, {
                    reset: true,
                    success: function () {
                        self.trigger('page_changed');
                    },
                    error: function () {
                        self.currentPage = oldPage;
                    }
                })
            },

            nextPage: function () {
                if (this.currentPage < this.totalPages - 1) {
                    this.setPage(this.currentPage + 1);
                }
            },

            previousPage: function () {
                if (this.currentPage > 0) {
                    this.setPage(this.currentPage - 1)
                }
            },

            sortDisplayName: function () {
                return '';
            },

            filterDisplayName: function () {
                return '';
            }
        })
    });
}).call(this, define || RequireJS.define);