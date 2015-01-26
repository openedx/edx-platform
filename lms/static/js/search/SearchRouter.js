;(function (define) {

define(['backbone'], function (Backbone) {
    'use strict';

    return Backbone.Router.extend({
      routes: {
        'search/:query': 'search'
      }
    });

});

})(define || RequireJS.define);
