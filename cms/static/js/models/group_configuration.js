define([
    'backbone', 'underscore', 'underscore.string', 'gettext', 'js/models/group',
    'js/collections/group', 'backbone.associations', 'coffee/src/main'
],
function(Backbone, _, str, gettext, GroupModel, GroupCollection) {
    'use strict';
    _.str = str;
    var GroupConfiguration = Backbone.AssociatedModel.extend({
        defaults: function() {
            return {
                name: '',
                description: '',
                groups: new GroupCollection([]),
                showGroups: false,
                editing: false
            };
        },

        relations: [{
            type: Backbone.Many,
            key: 'groups',
            relatedModel: GroupModel,
            collectionType: GroupCollection
        }],

        initialize: function() {
            this.setOriginalAttributes();
            return this;
        },

        setOriginalAttributes: function() {
            this._originalAttributes = this.toJSON();
        },

        reset: function() {
            this.set(this._originalAttributes);
        },

        isDirty: function() {
            return !_.isEqual(
                this._originalAttributes, this.toJSON()
            );
        },

        isEmpty: function() {
            return !this.get('name') && this.get('groups').isEmpty();
        },

        toJSON: function() {
            return {
                id: this.get('id'),
                name: this.get('name'),
                description: this.get('description'),
                groups: this.get('groups').toJSON()
            };
        },

        validate: function(attrs) {
            if (!_.str.trim(attrs.name)) {
                return {
                    message: gettext('Group Configuration name is required'),
                    attributes: {name: true}
                };
            }
        }
    });
    return GroupConfiguration;
});
