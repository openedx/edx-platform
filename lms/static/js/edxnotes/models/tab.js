;(function (define, undefined) {
'use strict';
define(['backbone'], function (Backbone) {
    var TabModel = Backbone.Model.extend({
        defaults: {
            'identifier': '',
            'name': '',
            'icon': '',
            'is_active': false,
            'is_closable': false
        },

        activate: function () {
            this.collection.each(_.bind(function(model) {
                // Inactivate all other models.
                if (model !== this) {
                    model.inactivate();
                }
            }, this));
            this.set('is_active', true);
        },

        inactivate: function () {
            this.set('is_active', false);
        },

        isActive: function () {
            return this.get('is_active');
        }
    });

    return TabModel;
});
}).call(this, define || RequireJS.define);
