(function(define) {
    define([
        'js/search/base/views/search_form'
    ], function(SearchForm) {
        'use strict';

        return SearchForm.extend({
            el: '#courseware-search-bar'
        });
    });
})(define || RequireJS.define);
