var edx = edx || {};

(function ($, Backbone) {
    'use strict'

    edx.search = edx.search || {};

    edx.search.SearchResult = Backbone.Model.extend({
        defaults: {
            location: {},
            contentType: '',
            excerpt: '',
        }
    });

})(jQuery, Backbone);
