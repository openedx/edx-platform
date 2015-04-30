;(function (define) {

define(['backbone'], function(Backbone) {
    'use strict';

    return function (Collection, SearchForm, ResultListView, searchQuery) {

        var collection = new Collection([]);
        var results = new ResultListView({ collection: collection });
        var dispatcher = _.clone(Backbone.Events);
        var form = new SearchForm();

        dispatcher.listenTo(form, 'search', function (query) {
            collection.performSearch(query);
            form.showLoadingIndicator();
        });

        dispatcher.listenTo(form, 'clear', function () {
            results.clearResults();
            form.hideClearAllButton();
        });

        dispatcher.listenTo(results, 'next', function () {
            collection.loadNextPage();
            form.showLoadingIndicator();
        });

        dispatcher.listenTo(collection, 'search', function () {
            if (collection.length > 0) {
                results.render();
                form.showClearAllButton();
            }
            else {
                form.showNotFoundMessage(collection.searchTerm);
            }
            form.hideLoadingIndicator();
        });

        dispatcher.listenTo(collection, 'next', function () {
            results.renderNext();
            form.hideLoadingIndicator();
        });

        dispatcher.listenTo(collection, 'error', function () {
            form.showErrorMessage();
            form.hideLoadingIndicator();
        });


        // kick off search if URL contains ?search_query=
        if (searchQuery) {
            form.doSearch(searchQuery);
        }

    };

});

})(define || RequireJS.define);
