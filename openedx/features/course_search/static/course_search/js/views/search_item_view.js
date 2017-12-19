/* globals Logger */

'use strict';

import 'jquery';
import _ from 'underscore';
import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

class SearchItemView extends Backbone.View {
  constructor(options) {
    const defaults = {
      tagName: 'li',
      className: 'search-results-item',
      attributes: {
        role: 'region',
        'aria-label': 'search result',
      },
      events: {
        click: 'logSearchItem',
      },
    };
    super(Object.assign({}, defaults, options));
  }

  initialize(options) {
    this.template = options.template;
  }

  render() {
    const data = _.clone(this.model.attributes);

    // Drop the preview text and result type if the search term is found
    // in the title/location in the course hierarchy
    if (this.model.get('content_type') === 'Sequence') {
      data.excerpt = '';
      data.content_type = '';
    }
    data.excerptHtml = HtmlUtils.HTML(data.excerpt);
    delete data.excerpt;
    HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.template)(data));
    return this;
  }

  /**
  * Redirect to a URL.  Mainly useful for mocking out in tests.
  * @param  {string} url The URL to redirect to.
  */
  static redirect(url) {
    window.location.href = url;
  }

  logSearchItem(event) {
    const target = this.model.id;
    const link = this.model.get('url');
    const collection = this.model.collection;
    const page = collection.page;
    const pageSize = collection.pageSize;
    const searchTerm = collection.searchTerm;
    const index = collection.indexOf(this.model);

    event.preventDefault();

    Logger.log('edx.course.search.result_selected', {
      search_term: searchTerm,
      result_position: (page * pageSize) + index,
      result_link: target,
    }).always(() => {
      SearchItemView.redirect(link);
    });
  }
}
export { SearchItemView as default };
