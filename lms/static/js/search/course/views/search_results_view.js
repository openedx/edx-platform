;(function (define) {

define([
    'js/search/base/views/search_results_view',
    'js/search/course/views/search_item_view'
], function (SearchResultsView, CourseSearchItemView) {
   'use strict';

    return SearchResultsView.extend({

        el: '#courseware-search-results',
        contentElement: '#course-content',
        resultsTemplateId: '#course_search_results-tpl',
        loadingTemplateId: '#search_loading-tpl',
        errorTemplateId: '#search_error-tpl',
        events: {
            'click .search-load-next': 'loadNext',
        },
        SearchItemView: CourseSearchItemView

    });

});


})(define || RequireJS.define);
