define([
    'backbone', 'underscore', 'gettext', 'js/models/group',
    'js/collections/group', 'backbone.associations', 'coffee/src/main'
],
function(Backbone, _, gettext, GroupModel, GroupCollection) {
    'use strict';
    var GroupConfiguration = Backbone.AssociatedModel.extend({
        defaults: function() {
            return {
                id: null,
                name: '',
                description: '',
                groups: new GroupCollection([{}, {}]),
                showGroups: false
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
            if (!attrs.name) {
                return {
                    message: gettext('Group Configuration name is required'),
                    attributes: {name: true}
                };
            }
            if (attrs.groups.length === 0) {
                return {
                    message: gettext('Please add at least one group'),
                    attributes: {groups: true}
                };
            } else {
                // validate all groups
                var invalidGroups = [];
                attrs.groups.each(function(group) {
                    if(!group.isValid()) {
                        invalidGroups.push(group);
                    }
                });
                if (!_.isEmpty(invalidGroups)) {
                    return {
                        message: gettext('All groups must have a name'),
                        attributes: {groups: invalidGroups}
                    };
                }
            }
        }
    });
    return GroupConfiguration;
});
