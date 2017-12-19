'use strict';

import Backbone from 'backbone';

class SearchResult extends Backbone.Model {
  constructor(attrs, ...args) {
    const defaults = {
      location: [],
      content_type: '',
      excerpt: '',
      url: '',
    };
    super(Object.assign({}, defaults, attrs), ...args);
  }
}
export { SearchResult as default };
