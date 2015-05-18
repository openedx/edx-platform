;(function (define) {

define(['backbone', 'course_discovery_meanings'], function(Backbone, meanings) {
    'use strict';

    return function (Collection, Form, ResultListView, FilterBarView, FacetsBarView, searchQuery) {
        //facet types configuration - set default display names
        var facetsTypes = meanings;

        var collection = new Collection([]);
        var results = new ResultListView({ collection: collection });
        var dispatcher = _.clone(Backbone.Events);
        var form = new Form();
        var filters = new FilterBarView();
        var facetsBarView = new FacetsBarView(facetsTypes);

        dispatcher.listenTo(form, 'search', function (query) {
            form.showLoadingIndicator();
            filters.changeQueryFilter(query);
        });

        dispatcher.listenTo(filters, 'search', function (searchTerm, facets) {
            collection.performSearch(searchTerm, facets);
            form.showLoadingIndicator();
        });

        dispatcher.listenTo(filters, 'clear', function () {
            form.clearSearch();
            collection.performSearch();
            filters.hideClearAllButton();
        });

        dispatcher.listenTo(results, 'next', function () {
            collection.loadNextPage();
            form.showLoadingIndicator();
        });

        dispatcher.listenTo(collection, 'search', function () {
            if (collection.length > 0) {
                results.render();
            }
            else {
                form.showNotFoundMessage(collection.searchTerm);
            }
            facetsBarView.renderFacets(collection.facets);
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

        dispatcher.listenTo(facetsBarView, 'addFilter', function (data) {
            filters.addFilter(data);
        });

        // kick off search on page refresh
        form.doSearch(searchQuery);

    };

});

})(define || RequireJS.define);
