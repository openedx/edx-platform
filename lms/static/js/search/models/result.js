var edx = edx || {};

(function (Backbone) {
    'use strict'

    edx.search = edx.search || {};

    edx.search.Result = Backbone.Model.extend({
        defaults: {
            location: {},
            content_type: '',
            excerpt: ''
        }
    });

})(Backbone);
