var edx = edx || {};

(function (Backbone) {
    'use strict'

    edx.search = edx.search || {};

    edx.search.Collection = Backbone.Collection.extend({
        model: edx.search.Result,
        pageSize: 20,
        totalCount: 0,
        searchTerm: '',
        page: 0,
        url: '/search',
        fetchXhr: null,

        performSearch: function (searchTerm) {
            this.page = 0;
            this.searchTerm = searchTerm;
            this.fetchXhr && this.fetchXhr.abort();
            this.fetchXhr = this.fetch({
                data: {
                    search_string: searchTerm,
                    page: 0
                },
                type: 'POST',
                success: function (self) {
                    self.trigger('search');
                },
                error: function (self) {
                    self.trigger('error');
                }
            });
        },

        loadNextPage: function () {
            this.fetchXhr && this.fetchXhr.abort();
            this.fetchXhr = this.fetch({
                data: {
                    search_string: this.searchTerm,
                    page: this.page + 1
                },
                type: 'POST',
                success: function (self) {
                    self.page += 1;
                    self.trigger('next')
                },
                error: function (self) {
                    self.trigger('error');
                }
            });
        },

        cancelSearch: function () {
            this.fetchXhr &&  this.fetchXhr.abort();
            this.page = 0;
            this.totalCount = 0;
        },

        parse: function(response) {
            this.totalCount = response.totalCount;
            return response.results;
        },

        hasNextPage: function () {
            return this.totalCount - ((this.page + 1) * this.pageSize) > 0;
        }

    });

})(Backbone);

