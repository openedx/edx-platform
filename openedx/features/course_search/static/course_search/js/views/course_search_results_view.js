'use strict';

import SearchResultsView from 'course_search/js/views/search_results_view';

import courseSearchResultsTemplate from 'text!course_search/templates/course_search_results.underscore';
import courseSearchItemTemplate from 'text!course_search/templates/course_search_item.underscore';

class CourseSearchResultsView extends SearchResultsView {
  constructor(options) {
    const defaults = {
      el: '.search-results',
      events: {
        'click .search-load-next': 'loadNext',
      },
    };
    super(Object.assign({}, defaults, options));

    this.contentElement = '#course-content';
    this.coursewareResultsWrapperElement = '.courseware-results-wrapper';
    this.resultsTemplate = courseSearchResultsTemplate;
    this.itemTemplate = courseSearchItemTemplate;
  }

  clear() {
    super.clear(this);
    $(this.coursewareResultsWrapperElement).hide();
    this.$contentElement.css('display', 'table-cell');
  }

  showResults() {
    super.showResults();
    $(this.coursewareResultsWrapperElement).css('display', 'table-cell');
  }
}
export { CourseSearchResultsView as default };
