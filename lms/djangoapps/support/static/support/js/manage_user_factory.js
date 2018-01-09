(function(define) {
    'use strict';

    define([
        'underscore',
        'support/js/views/manage_user'
    ], function(_, ManageUserView) {
        return function(options) {
            var params = _.extend({el: '.manage-user-content'}, options);
            return new ManageUserView(params).render();
        };
    });
}).call(this, define || RequireJS.define);
