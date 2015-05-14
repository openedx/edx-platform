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
        facetList: {},
        page: 0,
        url: '/search/course_discovery/',
        fetchXhr: null,

        performSearch: function (searchTerm, facets) {
            this.fetchXhr && this.fetchXhr.abort();
            this.searchTerm = searchTerm || '';
            this.facetList = facets || {};
            var data = this.preparePostData(0);
            this.resetState();
            this.fetchXhr = this.fetch({
                data: data,
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
            var data = this.preparePostData(this.page + 1);
            this.fetchXhr = this.fetch({
                data: data,
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

        preparePostData: function(pageNumber) {
            var data = {
                search_string: this.searchTerm,
                page_size: this.pageSize,
                page_index: pageNumber
            };
            if(this.facetList.length > 0) {
                this.facetList.each(function(facet) {
                    data[facet.get('type')] = facet.get('query');
                });
            }
            return data;
        },

        parse: function(response) {
            var results = response['results'] || [];
            this.latestModelsCount = results.length;
            this.totalCount = response.total;
            return _.map(results, function (result) {
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
