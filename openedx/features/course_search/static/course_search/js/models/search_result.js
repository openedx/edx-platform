(function(define) {
    'use strict';

    define(['backbone'], function(Backbone) {
        return Backbone.Model.extend({
            defaults: {
                location: [],
                content_type: '',
                excerpt: '',
                url: ''
            }
        });
    });
// eslint-disable-next-line no-undef
}(define || RequireJS.define));
