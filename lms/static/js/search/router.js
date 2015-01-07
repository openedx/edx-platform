
var edx = edx || {};

(function (Backbone) {
    'use strict';

    edx.search = edx.search || {};

    edx.search.Router = Backbone.Router.extend({
      routes: {
        'search/:query': 'search'
      }
    });

})(Backbone);
