;(function (define) {
    'use strict';

    define([
        'backbone',
        'js/search/dashboard/search_app',
        'js/search/base/routers/search_router',
        'js/search/dashboard/views/search_form',
        'js/search/base/collections/search_collection',
        'js/search/dashboard/views/search_results_view'
    ], function (Backbone, SearchApp, SearchRouter, DashSearchForm, SearchCollection, DashSearchResultsView) {

        return function () {
            var app = new SearchApp(
                SearchRouter,
                DashSearchForm,
                SearchCollection,
                DashSearchResultsView
            );
            Backbone.history.start();
        };
    });
}).call(this, define || RequireJS.define);
