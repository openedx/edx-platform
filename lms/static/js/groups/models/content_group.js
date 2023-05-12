(function(define) {
    'use strict';

    define(['backbone'], function(Backbone) {
        // eslint-disable-next-line no-var
        var ContentGroupModel = Backbone.Model.extend({
            idAttribute: 'id',
            defaults: {
                name: '',
                user_partition_id: null
            }
        });
        return ContentGroupModel;
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
