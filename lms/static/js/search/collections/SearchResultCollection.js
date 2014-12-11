var edx = edx || {};

(function ($, _, Backbone, gettext) {
    'use strict'

    var server = sinon.fakeServer.create();
    server.respondWith(
       [200, { "Content-Type": "application/json" },
        JSON.stringify(
            [{
                location: {'0': 'Example Week 2: Get Interactive', '1': 'Lesson 2: Let\'s Get Interactive', '2': 'Zooming Diagrams'},
                url: '/courses/edX/DemoX/Demo_Course/courseware/graded_interactions/simulations/',
                contentType: 'Course Text',
                excerpt: 'Welcome to the first week of the sample edX Course! '
                + 'We created this to give you “the basics” of how courses work at edX.'
                + 'Almost all edX courses have weeks, lessons, lectures, homework assignments, and exams.'
            }, {
                location: {'0': 'Example Week 2: Get Interactive', '1': 'Homework Labs and Demos', '2': 'Labs and Demos'},
                url: '/courses/edX/DemoX/Demo_Course/courseware/graded_interactions/graded_simulations/',
                contentType: 'Video',
                excerpt: 'Welcome to the first week of the sample edX Course! '
                + 'We created this to give you “the basics” of how courses work at edX.'
                + 'Almost all edX courses have weeks, lessons, lectures, homework assignments, and exams.'
            }, {
                location: {'0': 'Section', '1': 'Subsection', '2': 'Unit'},
                url: '/', contentType: 'Video',
                excerpt: 'Welcome to the first week of the sample edX Course! '
                + 'We created this to give you “the basics” of how courses work at edX.'
                + 'Almost all edX courses have weeks, lessons, lectures, homework assignments, and exams.'
            }]
        )
    ]);

    edx.search = edx.search || {};

    edx.search.SearchResultCollection = Backbone.Collection.extend({
        model: edx.search.SearchResult,
        pageSize: 20,
        totalCount: 0,
        page: 0,
        url: '/search',
        fetchXhr: null,

        performSearch: function (searchTerm) {
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
            this.trigger('searchRequest');
            this.reset();
            this.totalCount = 47;
            this.fetchXhr && this.fetchXhr.abort();
            this.fetchXhr = this.fetch({data: {page: 0}});

            var self = this;
            setTimeout(function() {
                server.respond();
                self.trigger('search');
            }, 2000)
>>>>>>> add loading message and ability to load more results, faking xhr with sinon.js /*
        },

        loadNextPage: function () {
            this.fetchXhr && this.fetchXhr.abort();
            this.fetchXhr = this.fetch({
                data: { page: this.page }
            });
            this.page += 1;

            var self = this;
            setTimeout(function() {
                server.respond();
                self.trigger('next');
            }, 2000)
        },

        cancelSearch: function () {
            this.fetchXhr &&  this.fetchXhr.abort();
            this.reset();
            this.page = 0;
            this.totalCount = 0;
        }

    });

})(jQuery, _, Backbone, gettext);

