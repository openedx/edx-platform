(function(define) {
    'use strict';

    define([
        'course_search/js/views/search_results_view',
        'text!course_search/templates/course_search_results.underscore',
        'text!course_search/templates/course_search_item.underscore'
    ], function(
        SearchResultsView,
        courseSearchResultsTemplate,
        courseSearchItemTemplate
    ) {
        return SearchResultsView.extend({
            el: '.search-results',
            contentElement: '#course-content',
            coursewareResultsWrapperElement: '.courseware-results-wrapper',
            resultsTemplate: courseSearchResultsTemplate,
            itemTemplate: courseSearchItemTemplate,
            events: {
                'click .search-load-next': 'loadNext'
            },

            clear: function() {
                SearchResultsView.prototype.clear.call(this);
                $(this.coursewareResultsWrapperElement).hide();
                this.$contentElement.css('display', 'table-cell');
            },

            showResults: function() {
                SearchResultsView.prototype.showResults.call(this);
                $(this.coursewareResultsWrapperElement).css('display', 'table-cell');
            }

        });
    });
}(define || RequireJS.define));
