define([
    'backbone',
    'js/programs/utils/auth_utils'
],
    function(Backbone, auth) {
        'use strict';

        return Backbone.Collection.extend(auth.autoSync);
    }
);
