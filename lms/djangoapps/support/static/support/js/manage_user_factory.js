(function(define) {
    'use strict';

    define([
        'underscore',
        'support/js/views/manage_user'
    ], function(_, ManageUserView) {
        return function(options) {
            // eslint-disable-next-line no-var
            var params = _.extend({el: '.manage-user-content'}, options);
            return new ManageUserView(params).render();
        };
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
