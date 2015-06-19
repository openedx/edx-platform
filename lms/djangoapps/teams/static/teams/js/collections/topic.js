;(function (define) {
    'use strict';
    define(['backbone.paginator', 'teams/js/models/topic'], function(BackbonePaginator, TopicModel) {
        var TopicCollection = BackbonePaginator.requestPager.extend({
            initialize: function(topics, options) {
                BackbonePaginator.requestPager.prototype.initialize.call(this);
                this.course_id = options.course_id;
                this.perPage = topics.results.length;
            },
            model: TopicModel,
            paginator_core: {
                type: 'GET',
                //accepts: 'application/json', // TODO: this argument just doesn't work when enabled (passes "undefined"). DRF does JSON by default. Is that good enough?
                dataType: 'json',
                url: function() {return this.url;}
            },
            paginator_ui: { // TODO: what is the significance of these values?
                firstPage: 1,
                currentPage: 1,
                perPage: function() {return this.perPage;}
            },
            sort_field: 'name',
            sortDisplayName: function() {return this.sort_field;},
            server_api: {
                'course_id': function() {return this.course_id;},
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
            },

            hasPreviousPage: function () {
                return this.firstPage < this.currentPage;
            },

            hasNextPage: function () {
                return this.currentPage + (1 - this.firstPage) < this.totalPages;
            },

            setPage: function (page) {
                var oldPage = this.currentPage,
                    self = this;
                this.goTo(page, {
                    reset: true,
                    success: function () {
                        self.trigger('page_changed');
                        self.trigger('reset');
                        self.trigger('sync');
                    },
                    error: function () {
                        self.currentPage = oldPage;
                    }
                });
            },

            nextPage: function () {
                if (this.hasNextPage()) {
                    this.setPage(this.currentPage + 1);
                }
            },

            previousPage: function () {
                if (this.hasPreviousPage()) {
                    this.setPage(this.currentPage - 1);
                }
            }
        });
        return TopicCollection;
    });
}).call(this, define || RequireJS.define);
