'use strict';

import SearchResultsView from 'course_search/js/views/search_results_view';

import dashboardSearchResultsTemplate from 'text!course_search/templates/dashboard_search_results.underscore';
import dashboardSearchItemTemplate from 'text!course_search/templates/dashboard_search_item.underscore';

class DashboardSearchResultsView extends SearchResultsView {
  constructor(options) {
    const defaults = {
      el: '.search-results',
      events: {
        'click .search-load-next': 'loadNext',
      },
    };
    super(Object.assign({}, defaults, options));

    this.resultsTemplate = dashboardSearchResultsTemplate;
    this.itemTemplate = dashboardSearchItemTemplate;
  }

  backToCourses() {
    this.clear();
    this.trigger('reset');
    return false;
  }
}
export { DashboardSearchResultsView as default };
