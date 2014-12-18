var edx = edx || {};

(function(Backbone) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.ContentGroupModel = Backbone.Model.extend({
        idAttribute: 'id',
        defaults: {
            name: ''
        }
    });
}).call(this, Backbone);
