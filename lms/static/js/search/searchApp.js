
var edx = edx || {};

(function($) {
    'use strict';

    edx.search = edx.search || {};

    var model = new edx.search.SearchResult;
    var collection = new edx.search.SearchResultCollection();
    var searchFormView = new edx.search.SearchFormView({ collection: collection });
    var searchResultsView = new edx.search.SearchResultsView({ collection: collection });

    searchFormView.on('SearchFormView:clearSearch', function () {
        searchResultsView.clearSearchResults();
    });

    // TODO
    // search spinner (and cancel button?)


})(jQuery);
