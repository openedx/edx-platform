'use strict';

import Backbone from 'backbone';

class SearchRouter extends Backbone.Router {
  constructor() {
    super({ routes: {
      'search/:query': 'search',
    } });
  }

  search(query) {
    this.trigger('search', query);
  }
}
export { SearchRouter as default };
