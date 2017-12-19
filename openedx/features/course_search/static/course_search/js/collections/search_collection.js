'use strict';

import _ from 'underscore';
import Backbone from 'backbone';

import SearchResult from 'course_search/js/models/search_result';

class SearchCollection extends Backbone.Collection {
  initialize(models, options) {
    this.model = SearchResult;
    this.pageSize = 20;
    this.totalCount = 0;
    this.latestModelsCount = 0;
    this.accessDeniedCount = 0;
    this.searchTerm = '';
    this.page = 0;
    this.fetchXhr = null;
    this.url = '/search/';
    if (options && options.courseId) {
      this.url += options.courseId;
    }
    super.initialize(models, options);
  }

  performSearch(searchTerm) {
    if (this.fetchXhr) {
      this.fetchXhr.abort();
    }
    this.searchTerm = searchTerm || '';
    this.resetState();
    this.fetchXhr = this.fetch({
      data: {
        search_string: searchTerm,
        page_size: this.pageSize,
        page_index: 0,
      },
      type: 'POST',
      success(self) {
        self.trigger('search');
      },
      error(self) {
        self.trigger('error');
      },
    });
  }

  loadNextPage() {
    if (this.fetchXhr) {
      this.fetchXhr.abort();
    }
    this.fetchXhr = this.fetch({
      data: {
        search_string: this.searchTerm,
        page_size: this.pageSize,
        page_index: this.page + 1,
      },
      type: 'POST',
      success(self) {
        self.page += 1;  // eslint-disable-line no-param-reassign
        self.trigger('next');
      },
      error(self) {
        self.trigger('error');
      },
      add: true,
      reset: false,
      remove: false,
    });
  }

  cancelSearch() {
    if (this.fetchXhr) {
      this.fetchXhr.abort();
    }
    this.resetState();
  }

  parse(response) {
    this.latestModelsCount = response.results.length;
    this.totalCount = response.total;
    this.accessDeniedCount += response.access_denied_count;
    this.totalCount -= this.accessDeniedCount;
    return _.map(response.results, result => result.data);
  }

  resetState() {
    this.page = 0;
    this.totalCount = 0;
    this.latestModelsCount = 0;
    this.accessDeniedCount = 0;
    // empty the entire collection
    this.reset();
  }

  hasNextPage() {
    return this.totalCount - ((this.page + 1) * this.pageSize) > 0;
  }

  latestModels() {
    return this.last(this.latestModelsCount);
  }
}
export { SearchCollection as default };
