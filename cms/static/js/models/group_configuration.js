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
                version: null,
                groups: new GroupCollection([
                    {
                        name: gettext('Group A'),
                        order: 0
                    },
                    {
                        name: gettext('Group B'),
                        order: 1
                    }
                ]),
                showGroups: false,
                editing: false,
                usage: []
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
            this._originalAttributes = this.parse(this.toJSON());
        },

        reset: function() {
            this.set(this._originalAttributes, { parse: true });
        },

        isDirty: function() {
            return !_.isEqual(
                this._originalAttributes, this.parse(this.toJSON())
            );
        },

        isEmpty: function() {
            return !this.get('name') && this.get('groups').isEmpty();
        },

        parse: function(response) {
            var attrs = $.extend(true, {}, response);

            _.each(attrs.groups, function(group, index) {
                group.order = group.order || index;
            });

            return attrs;
        },

        toJSON: function() {
            return {
                id: this.get('id'),
                name: this.get('name'),
                description: this.get('description'),
                version: this.get('version'),
                groups: this.get('groups').toJSON()
            };
        },

        validate: function(attrs) {
            if (!_.str.trim(attrs.name)) {
                return {
                    message: gettext('Group Configuration name is required.'),
                    attributes: {name: true}
                };
            }

            if (attrs.groups.length < 1) {
                return {
                    message: gettext('There must be at least one group.'),
                    attributes: { groups: true }
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
                        message: gettext('All groups must have a name.'),
                        attributes: { groups: invalidGroups }
                    };
                }
            }
        }
    });

    return GroupConfiguration;
});
