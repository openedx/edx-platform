;(function (define) {

define(['backbone'], function(Backbone) {
    'use strict';

    return function (Collection, DiscoveryForm, ResultListView) {

        var collection = new Collection([]);
        var results = new ResultListView({ collection: collection });
        var dispatcher = _.clone(Backbone.Events);
        var form = new DiscoveryForm();

        dispatcher.listenTo(form, 'search', function (query) {
            results.showLoadingMessage();
            collection.performSearch(query);
        });

        dispatcher.listenTo(form, 'clear', function () {
            collection.cancelSearch();
            results.clear();
        });

        dispatcher.listenTo(results, 'next', function () {
            collection.loadNextPage();
        });

    };

});

})(define || RequireJS.define);
