var edx = edx || {};

(function ($, _, Backbone, gettext) {
    'use strict'

    edx.search = edx.search || {};

    edx.search.SearchResultCollection = Backbone.Collection.extend({
        model: edx.search.SearchResult,
        pageSize: 20,
        totalCount: 0,
        nextPage: 1,

        performSearch: function (searchTerm) {
            this.totalCount = 47;
            this.reset([
                {
                    location: {
                        '0': 'Example Week 2: Get Interactive',
                        '1': 'Lesson 2: Let\'s Get Interactive',
                        '2': 'Zooming Diagrams'
                    },
                    url: '/courses/edX/DemoX/Demo_Course/courseware/graded_interactions/simulations/',
                    contentType: 'Course Text',
                    excerpt: 'Welcome to the first week of the sample edX Course! '+
                        'We created this to give you “the basics” of how courses work at edX.' +
                        'Almost all edX courses have weeks, lessons, lectures, homework assignments, and exams.',
                },
                {
                    location: {
                        '0': 'Example Week 2: Get Interactive',
                        '1': 'Homework Labs and Demos',
                        '2': 'Labs and Demos'
                    },
                    url: '/courses/edX/DemoX/Demo_Course/courseware/graded_interactions/graded_simulations/',
                    contentType: 'Video',
                    excerpt: 'Welcome to the first week of the sample edX Course! '+
                        'We created this to give you “the basics” of how courses work at edX.' +
                        'Almost all edX courses have weeks, lessons, lectures, homework assignments, and exams.',
                },
                {
                    location: {
                        '0': 'Section',
                        '1': 'Subsection',
                        '2': 'Unit'
                    },
                    url: '/',
                    contentType: 'Video',
                    excerpt: 'Welcome to the first week of the sample edX Course! '+
                        'We created this to give you “the basics” of how courses work at edX.' +
                        'Almost all edX courses have weeks, lessons, lectures, homework assignments, and exams.',
                }
            ]);
            this.trigger('sync');
        },

        loadMore: function () {

        }
    });

})(jQuery, _, Backbone, gettext);

