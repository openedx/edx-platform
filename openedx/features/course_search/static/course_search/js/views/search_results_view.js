/* globals ngettext */

'use strict';

import 'jquery';
import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';
import SearchItemView from 'course_search/js/views/search_item_view';
import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';

import searchLoadingTemplate from 'text!course_search/templates/search_loading.underscore';
import searchErrorTemplate from 'text!course_search/templates/search_error.underscore';

class SearchResultsView extends Backbone.View {
  constructor(options) {
    // these defaults should be defined by subclasses
    const defaults = {
      el: '',
      events: {},
    };
    super(Object.assign({}, defaults, options));

    // these properties should be defined by subclasses
    this.contentElement = '';
    this.resultsTemplate = null;
    this.itemTemplate = null;

    this.loadingTemplate = searchLoadingTemplate;
    this.errorTemplate = searchErrorTemplate;
    this.spinner = '.search-load-next .icon';
  }

  initialize() {
    this.$contentElement = this.contentElement ? $(this.contentElement) : $([]);
  }

  render() {
    HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.resultsTemplate)({
      totalCount: this.collection.totalCount,
      totalCountMsg: this.totalCountMsg(),
      pageSize: this.collection.pageSize,
      hasMoreResults: this.collection.hasNextPage(),
    }));
    this.renderItems();
    this.$el.find(this.spinner).hide();
    this.showResults();
    return this;
  }

  renderNext() {
    // total count may have changed
    this.$el.find('.search-count').text(this.totalCountMsg());
    this.renderItems();
    if (!this.collection.hasNextPage()) {
      this.$el.find('.search-load-next').remove();
    }
    this.$el.find(this.spinner).hide();
  }

  renderItems() {
    const latest = this.collection.latestModels();
    const items = latest.map((result) => {
      const item = new SearchItemView({
        model: result,
        template: this.itemTemplate,
      });
      return item.render().el;
    }, this);
    // xss-lint: disable=javascript-jquery-append
    this.$el.find('ol').append(items);
  }

  totalCountMsg() {
    const fmt = ngettext('{total_results} result', '{total_results} results', this.collection.totalCount);
    return StringUtils.interpolate(fmt, {
      total_results: this.collection.totalCount,
    });
  }

  clear() {
    this.$el.hide().empty();
    this.$contentElement.show();
  }

  showResults() {
    this.$el.show();
    this.$contentElement.hide();
  }

  showLoadingMessage() {
    // Empty any previous loading/error message
    $('#loading-message').html('');
    $('#error-message').html('');

    // Show the loading message
    HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.loadingTemplate)());

    // Show the results
    this.showResults();
  }

  showErrorMessage() {
    HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.errorTemplate)());
    this.showResults();
  }

  loadNext(event) {
    if (event) {
      event.preventDefault();
    }
    this.$el.find(this.spinner).show();
    this.trigger('next');
    return false;
  }
}
export { SearchResultsView as default };
