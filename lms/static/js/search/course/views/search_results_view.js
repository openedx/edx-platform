;(function (define) {

define([
    'js/search/base/views/search_results_view',
    'js/search/course/views/search_item_view'
], function (SearchResultsView, CourseSearchItemView) {
   'use strict';

    return SearchResultsView.extend({

        el: '.courseware-results',
        contentElement: '#course-content',
        coursewareResultsWrapperElement: '.courseware-results-wrapper',
        resultsTemplateId: '#course_search_results-tpl',
        loadingTemplateId: '#search_loading-tpl',
        errorTemplateId: '#search_error-tpl',
        events: {
            'click .search-load-next': 'loadNext',
        },
        SearchItemView: CourseSearchItemView,

        clear: function () {
            SearchResultsView.prototype.clear.call(this);
            $(this.coursewareResultsWrapperElement).hide();
            this.$contentElement.css('display', 'table-cell');
        },

        showResults: function () {
            SearchResultsView.prototype.showResults.call(this);
            $(this.coursewareResultsWrapperElement).css('display', 'table-cell');
        }

    });

});


})(define || RequireJS.define);
