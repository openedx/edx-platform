
var edx = edx || {};

(function() {
    'use strict';

    edx.search = edx.search || {};

    var form = new edx.search.Form();
    var collection = new edx.search.Collection();
    var results = new edx.search.List({ collection: collection });

    form.on('search', collection.performSearch, collection);
    form.on('search', results.showLoadingMessage, results);

    form.on('clear', collection.cancelSearch, collection);
    form.on('clear', results.clear, results);

    results.on('next', collection.loadNextPage, collection);

})();
