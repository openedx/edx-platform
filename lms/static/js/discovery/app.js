;(function (define) {

define(['backbone'], function(Backbone) {
    'use strict';

    return function (Collection, DiscoveryForm, ResultListView) {

        var collection = new Collection([]);
        var results = new ResultListView({ collection: collection });
        var dispatcher = _.clone(Backbone.Events);
        var form = new DiscoveryForm();

        dispatcher.listenTo(form, 'search', function (query) {
            results.showLoadingIndicator();
            collection.performSearch(query);
        });

        dispatcher.listenTo(form, 'clear', function () {
            collection.cancelSearch();
            form.hideClearAllButton();
            results.clear();
        });

        dispatcher.listenTo(results, 'next', function () {
            collection.loadNextPage();
        });

        dispatcher.listenTo(collection, 'search', function () {
            form.showClearAllButton();
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
