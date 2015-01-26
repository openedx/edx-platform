;(function (define) {

define(['backbone'], function (Backbone) {
    'use strict';

    return Backbone.Model.extend({
        defaults: {
            location: [],
            content_type: '',
            excerpt: '',
            url: ''
        }
    });

});

})(define || RequireJS.define);
