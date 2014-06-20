define([
    'backbone', 'gettext', 'backbone.associations'
], function(Backbone, gettext) {
    'use strict';
    var Group = Backbone.AssociatedModel.extend({
        defaults: function() {
            return { name: '' };
        },

        isEmpty: function() {
            return !this.get('name');
        },

        toJSON: function() {
            return { name: this.get('name') };
        },

        validate: function(attrs) {
            if (!attrs.name) {
                return {
                    message: gettext('Group name is required'),
                    attributes: { name: true }
                };
            }
        }
    });

    return Group;
});
