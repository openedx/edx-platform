;(function (define) {
    'use strict';

    define(['backbone', 'js/search/base/routers/search_router', 'js/search/course/views/search_form',
            'js/search/base/collections/search_collection', 'js/search/course/views/search_results_view'],
        function(Backbone, SearchRouter, CourseSearchForm, SearchCollection, SearchResultsView) {

            return function (courseId) {

                var router = new SearchRouter();
                var form = new CourseSearchForm();
                var collection = new SearchCollection([], { courseId: courseId });
                var results = new SearchResultsView({ collection: collection });
                var dispatcher = _.clone(Backbone.Events);

                dispatcher.listenTo(router, 'search', function (query) {
                    form.doSearch(query);
                });

                dispatcher.listenTo(form, 'search', function (query) {
                    results.showLoadingMessage();
                    collection.performSearch(query);
                    router.navigate('search/' + query, { replace: true });
                });

                dispatcher.listenTo(form, 'clear', function () {
                    collection.cancelSearch();
                    results.clear();
                    router.navigate('');
                });

                dispatcher.listenTo(results, 'next', function () {
                    collection.loadNextPage();
                });

                dispatcher.listenTo(collection, 'search', function () {
                    results.render();
                });

                dispatcher.listenTo(collection, 'next', function () {
                    results.renderNext();
                });

                dispatcher.listenTo(collection, 'error', function () {
                    results.showErrorMessage();
                });

            };

        });

})(define || RequireJS.define);
