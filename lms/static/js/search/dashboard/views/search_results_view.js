(function(define) {
    define([
        'js/search/base/views/search_results_view',
        'js/search/dashboard/views/search_item_view'
    ], function(SearchResultsView, DashSearchItemView) {
        'use strict';

        return SearchResultsView.extend({

            el: '#dashboard-search-results',
            contentElement: '#my-courses, #profile-sidebar',
            resultsTemplateId: '#dashboard_search_results-tpl',
            loadingTemplateId: '#search_loading-tpl',
            errorTemplateId: '#search_error-tpl',
            events: {
                'click .search-load-next': 'loadNext',
                'click .search-back-to-courses': 'backToCourses'
            },
            SearchItemView: DashSearchItemView,

            backToCourses: function() {
                this.clear();
                this.trigger('reset');
                return false;
            }

        });
    });
})(define || RequireJS.define);
