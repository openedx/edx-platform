(function(define) {
    'use strict';

    define([
        'underscore', 'backbone', 'course_search/js/search_router', 'course_search/js/views/search_form',
        'course_search/js/collections/search_collection', 'course_search/js/views/course_search_results_view'
    ],
    function(_, Backbone, SearchRouter, CourseSearchForm, SearchCollection, CourseSearchResultsView) {
        return function(options) {
            var courseId = options.courseId;
            var requestedQuery = options.query;
            var supportsActive = options.supportsActive;
            var router = new SearchRouter();
            var form = new CourseSearchForm({
                el: options.searchHeader,
                supportsActive: supportsActive
            });
            var collection = new SearchCollection([], {courseId: courseId});
            var results = new CourseSearchResultsView({collection: collection});
            var dispatcher = _.clone(Backbone.Events);

            dispatcher.listenTo(router, 'search', function(query) {
                form.doSearch(query);
            });

            dispatcher.listenTo(form, 'search', function(query) {
                results.showLoadingMessage();
                collection.performSearch(query);
                router.navigate('search/' + query, {replace: true});
            });

            dispatcher.listenTo(form, 'clear', function() {
                collection.cancelSearch();
                results.clear();
                router.navigate('');
            });

            dispatcher.listenTo(results, 'next', function() {
                collection.loadNextPage();
            });

            dispatcher.listenTo(collection, 'search', function() {
                results.render();
            });

            dispatcher.listenTo(collection, 'next', function() {
                results.renderNext();
            });

            dispatcher.listenTo(collection, 'error', function() {
                results.showErrorMessage();
            });

            // Perform a search if an initial query has been provided.
            if (requestedQuery) {
                router.trigger('search', requestedQuery);
            }
        };
    }
    );
}).call(this, define || RequireJS.define);
