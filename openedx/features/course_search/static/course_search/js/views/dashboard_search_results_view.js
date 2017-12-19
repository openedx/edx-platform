(function(define) {
    'use strict';

    define([
        'course_search/js/views/search_results_view',
        'text!course_search/templates/dashboard_search_results.underscore',
        'text!course_search/templates/dashboard_search_item.underscore'
    ], function(
        SearchResultsView,
        dashboardSearchResultsTemplate,
        dashboardSearchItemTemplate
    ) {
        return SearchResultsView.extend({
            el: '.search-results',
            resultsTemplate: dashboardSearchResultsTemplate,
            itemTemplate: dashboardSearchItemTemplate,
            events: {
                'click .search-load-next': 'loadNext'
            },

            backToCourses: function() {
                this.clear();
                this.trigger('reset');
                return false;
            }

        });
    });
}(define || RequireJS.define));
