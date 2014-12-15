var edx = edx || {};

(function ($, _, Backbone, gettext) {
    'use strict'

    var server = sinon.fakeServer.create();
    server.respondWith("POST", "/search", [
        200, { "Content-Type": "application/json" },
        JSON.stringify({
            totalCount: 35,
            results: [{
                location: {'0': 'Example Week 2: Get Interactive', '1': 'Lesson 2: Let\'s Get Interactive', '2': 'Zooming Diagrams'},
                url: '/courses/edX/DemoX/Demo_Course/courseware/graded_interactions/simulations/',
                contentType: 'Course Text',
                excerpt: '1 --- Welcome to the first week of the sample edX Course! '
                + 'We created this to give you “the basics” of how courses work at edX.'
                + 'Almost all edX courses have weeks, lessons, lectures, homework assignments, and exams. '
            }, {
                location: {'0': 'Example Week 2: Get Interactive', '1': 'Homework Labs and Demos', '2': 'Labs and Demos'},
                url: '/courses/edX/DemoX/Demo_Course/courseware/graded_interactions/graded_simulations/',
                contentType: 'Video',
                excerpt: '2 - Welcome to the first week of the sample edX Course! '
                + 'We created this to give you “the basics” of how courses work at edX.'
                + 'Almost all edX courses have weeks, lessons, lectures, homework assignments, and exams. '
            }, {
                location: {'0': 'Section', '1': 'Subsection', '2': 'Unit'},
                url: '/', contentType: 'Video',
                excerpt: '3 - Welcome to the first week of the sample edX Course! '
                + 'We created this to give you “the basics” of how courses work at edX.'
                + 'Almost all edX courses have weeks, lessons, lectures, homework assignments, and exams. '
            }]
        })
    ]);
    server.autoRespond = true;
    server.autoRespondAfter = 1000; // ms

    edx.search = edx.search || {};

    edx.search.SearchResultCollection = Backbone.Collection.extend({
        model: edx.search.SearchResult,
        pageSize: 20,
        totalCount: 0,
        searchTerm: '',
        page: 0,
        url: '/search',
        fetchXhr: null,

        performSearch: function (searchTerm) {
<<<<<<< HEAD
            var self = this;
            $.ajax({
                type: 'POST',
                dataType: 'json',
                contentType: 'application/json',
                url: "/search",
                data: {
                search_string: searchTerm
                },
                success: function(data){
                    self.totalCount = data.total;
                    var results_array = data.results;
                    var data_array = [];
                    for(var i=0; i<results_array.length; ++i){
                        data_array.push(results_array[i].data);
                    }
                    self.reset(data_array);
                    self.trigger('sync');
                },
                error: function(){
                    alert('error running search');
                }
            });
/* Test here loading message and ability to load more results, faking xhr with sinon.js
            this.page = 0;
            this.searchTerm = searchTerm;
            this.trigger('searchRequest');
            this.fetchXhr && this.fetchXhr.abort();
            this.fetchXhr = this.fetch({
                data: { search_string: searchTerm, page: 0 },
                type: 'POST',
                success: function (self) {
                    self.trigger('search');
                },
                error: function () {
                    self.trigger('error');
                }
            });
            this.fetchXhr.done();
>>>>>>> simple paging
>>>>>>> add loading message and ability to load more results, faking xhr with sinon.js */
        },

        loadNextPage: function () {
            this.fetchXhr && this.fetchXhr.abort();
            this.fetchXhr = this.fetch({
                data: { search_string: this.searchTerm, page: this.page + 1 },
                type: 'POST',
                success: function (self) {
                    self.page += 1;
                    self.trigger('next');
                },
                error: function () {
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

        hasMoreResults: function () {
            return this.totalCount - ((this.page + 1) * this.pageSize) > 0;
        }

    });

})(jQuery, _, Backbone, gettext);

