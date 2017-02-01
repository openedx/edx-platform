define([
    'backbone', 'underscore', 'underscore.string', 'gettext',
    'backbone.associations'
], function(Backbone, _, str, gettext) {
    'use strict';
    var Group = Backbone.AssociatedModel.extend({
        defaults: function() {
            return {
                name: '',
                version: 1,
                order: null,
                usage: []
            };
        },
        url: function() {
            var parentModel = this.collection.parents[0];
            return parentModel.urlRoot + '/' + encodeURIComponent(parentModel.id) + '/' + encodeURIComponent(this.id);
        },

        reset: function() {
            this.set(this._originalAttributes, {parse: true});
        },

        isEmpty: function() {
            return !this.get('name');
        },

        toJSON: function() {
            return {
                id: this.get('id'),
                name: this.get('name'),
                version: this.get('version'),
                usage: this.get('usage')
            };
        },

        validate: function(attrs) {
            if (!str.trim(attrs.name)) {
                return {
                    message: gettext('Group name is required'),
                    attributes: {name: true}
                };
            }
        }
    });

    return Group;
});
