;(function (define) {

define([
    'backbone',
    'js/discovery/result'
], function (Backbone, Result) {
    'use strict';

    return Backbone.Collection.extend({

        model: Result,
        pageSize: 20,
        totalCount: 0,
        latestModelsCount: 0,
        searchTerm: '',
        page: 0,
        url: '/search/course_discovery',
        fetchXhr: null,

        performSearch: function (searchTerm) {
            this.fetchXhr && this.fetchXhr.abort();
            this.searchTerm = searchTerm || '';
            this.resetState();
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
                },
                add: true,
                reset: false,
                remove: false
            });
        },

        cancelSearch: function () {
            this.fetchXhr && this.fetchXhr.abort();
            this.resetState();
        },

        parse: function(response) {
            this.latestModelsCount = response.results.length;
            this.totalCount = response.total;
            console.log(response)
            return _.map(response.results, function (result) {
                return result.data;
            });
        },

        resetState: function () {
            this.reset();
            this.page = 0;
            this.totalCount = 0;
            this.latestModelsCount = 0;
        },

        hasNextPage: function () {
            return this.totalCount - ((this.page + 1) * this.pageSize) > 0;
        },

        latestModels: function () {
            return this.last(this.latestModelsCount);
        }

    });

});


})(define || RequireJS.define);
