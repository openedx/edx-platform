define([
    'backbone', 'underscore', 'gettext', 'js/models/group', 'js/collections/group',
    'backbone.associations', 'coffee/src/main'
],
function(Backbone, _, gettext, GroupModel, GroupCollection) {
    'use strict';
    var GroupConfiguration = Backbone.AssociatedModel.extend({
        defaults: function() {
            return {
                name: '',
                scheme: 'random',
                description: '',
                version: 2,
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

        initialize: function(attributes, options) {
            this.on('remove:groups', this.groupRemoved);

            this.canBeEmpty = options && options.canBeEmpty;
            this.setOriginalAttributes();

            return this;
        },

        setOriginalAttributes: function() {
            this._originalAttributes = this.parse(this.toJSON());
        },

        reset: function() {
            this.set(this._originalAttributes, {parse: true, validate: true});
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
                scheme: this.get('scheme'),
                description: this.get('description'),
                version: this.get('version'),
                groups: this.get('groups').toJSON()
            };
        },

        validate: function(attrs) {
            if (!attrs.name.trim()) {
                return {
                    message: gettext('Group Configuration name is required.'),
                    attributes: {name: true}
                };
            }

            if (!this.canBeEmpty && attrs.groups.length < 1) {
                return {
                    message: gettext('There must be at least one group.'),
                    attributes: {groups: true}
                };
            } else {
                // validate all groups
                var validGroups = new Backbone.Collection(),
                    invalidGroups = new Backbone.Collection();
                attrs.groups.each(function(group) {
                    if (!group.isValid()) {
                        invalidGroups.add(group);
                    } else {
                        validGroups.add(group);
                    }
                });

                if (!invalidGroups.isEmpty()) {
                    return {
                        message: gettext('All groups must have a name.'),
                        attributes: {groups: invalidGroups.toJSON()}
                    };
                }

                var groupNames = validGroups.map(function(group) { return group.get('name'); });
                if (groupNames.length !== _.uniq(groupNames).length) {
                    return {
                        message: gettext('All groups must have a unique name.'),
                        attributes: {groups: validGroups.toJSON()}
                    };
                }
            }
        },

        groupRemoved: function() {
            this.setOriginalAttributes();
        }
    });

    return GroupConfiguration;
});
