;(function (define) {
    'use strict';
    define(['backbone'], function(Backbone) {
        var ContentGroupModel = Backbone.Model.extend({
            idAttribute: 'id',
            defaults: {
                name: '',
                user_partition_id: null
            }
        });
        return ContentGroupModel;
    });
}).call(this, define || RequireJS.define);
