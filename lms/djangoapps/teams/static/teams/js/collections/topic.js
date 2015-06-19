;(function (define) {
    'use strict';
    define(['backbone.paginator', 'teams/js/models/topic'], function(BackbonePaginator, TopicModel) {
        var TopicCollection = BackbonePaginator.requestPager.extend({
            model: TopicModel,
            paginator_core: {
                type: 'GET',
                accepts: 'application/json',
                dataType: 'json',
                url: function() {return this.url;}
            },
            paginator_ui: { // TODO: what is the significance of these values?
                firstPage: 1,
                currentPage: 1,
                perPage: 50
            },
            sort_field: 'name',
            sortDisplayName: function() {return this.sort_field;},
            server_api: {
                'order_by': function() {return this.sort_field;},
                'page_size': function() {return this.perPage;},
                'page': function() {return this.currentPage;}
            },

            parse: function(response) {
                this.totalCount = response.count;
                this.currentPage = response.current_page;
                this.totalPages = response.num_pages;
                this.start = response.start;
                return response.results;
            }
        });
        return TopicCollection;
    });
}).call(this, define || RequireJS.define);
