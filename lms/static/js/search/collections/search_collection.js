;(function (define) {

define([
    'backbone',
    'js/search/models/search_result'
], function (Backbone, SearchResult) {
    'use strict';

    return Backbone.Collection.extend({

        model: SearchResult,
        pageSize: 20,
        totalCount: 0,
        accessDeniedCount: 0,
        searchTerm: '',
        page: 0,
        url: '/search/',
        fetchXhr: null,

        initialize: function (models, options) {
            // call super constructor
            Backbone.Collection.prototype.initialize.apply(this, arguments);
            if (options && options.course_id) {
                this.url += options.course_id;
            }
        },

        performSearch: function (searchTerm) {
            this.fetchXhr && this.fetchXhr.abort();
            this.searchTerm = searchTerm || '';
            this.totalCount = 0;
            this.accessDeniedCount = 0;
            this.page = 0;
            this.fetchXhr = this.fetch({
                data: {
                    search_string: searchTerm,
                    page_size: this.pageSize,
                    page_index: 0
                },
                type: 'POST',
                success: function (self, xhr) {
                    self.trigger('search');
                },
                error: function (self, xhr) {
                    self.trigger('error');
                }
            });
        },

        loadNextPage: function () {
            this.fetchXhr && this.fetchXhr.abort();
            this.fetchXhr = this.fetch({
                data: {
                    search_string: this.searchTerm,
                    page_size: this.pageSize,
                    page_index: this.page + 1
                },
                type: 'POST',
                success: function (self, xhr) {
                    self.page += 1;
                    self.trigger('next');
                },
                error: function (self, xhr) {
                    self.trigger('error');
                }
            });
        },

        cancelSearch: function () {
            this.fetchXhr && this.fetchXhr.abort();
            this.page = 0;
            this.totalCount = 0;
            this.accessDeniedCount = 0;
        },

        parse: function(response) {
            this.totalCount = response.total;
            this.accessDeniedCount += response.access_denied_count;
            this.totalCount -= this.accessDeniedCount;
            return _.map(response.results, function(result){ return result.data; });
        },

        hasNextPage: function () {
            return this.totalCount - ((this.page + 1) * this.pageSize) > 0;
        }

    });

});


})(define || RequireJS.define);
