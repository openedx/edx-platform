/**
 * This class defines an editing view for content experiment group configurations.
 * It is expected to be backed by a GroupConfiguration model.
 */
define([
    'js/views/list_item_editor', 'underscore', 'jquery', 'gettext',
    'js/views/experiment_group_edit'
],
function(ListItemEditorView, _, $, gettext, ExperimentGroupEditView) {
    'use strict';
    var GroupConfigurationEditorView = ListItemEditorView.extend({
        tagName: 'div',
        events: {
            'change .collection-name-input': 'setName',
            'change .group-configuration-description-input': 'setDescription',
            'click .action-add-group': 'createGroup',
            'focus .input-text': 'onFocus',
            'blur .input-text': 'onBlur',
            'submit': 'setAndClose',
            'click .action-cancel': 'cancel'
        },

        className: function () {
            var index = this.model.collection.indexOf(this.model);

            return [
                'collection-edit',
                'group-configuration-edit',
                'group-configuration-edit-' + index
            ].join(' ');
        },

        initialize: function() {
            var groups = this.model.get('groups');

            ListItemEditorView.prototype.initialize.call(this);

            this.template = this.loadTemplate('group-configuration-editor');
            this.listenTo(groups, 'add', this.onAddItem);
            this.listenTo(groups, 'reset', this.addAll);
            this.listenTo(groups, 'all', this.render);
        },

        render: function() {
            ListItemEditorView.prototype.render.call(this);
            this.addAll();
            return this;
        },

        getTemplateOptions: function() {
            return {
                id: this.model.get('id'),
                uniqueId: _.uniqueId(),
                name: this.model.escape('name'),
                description: this.model.escape('description'),
                usage: this.model.get('usage'),
                isNew: this.model.isNew()
            };
        },

        getSaveableModel: function() {
            return this.model;
        },

        onAddItem: function(group) {
            var view = new ExperimentGroupEditView({ model: group });
            this.$('ol.groups').append(view.render().el);

            return this;
        },

        addAll: function() {
            this.model.get('groups').each(this.onAddItem, this);
        },

        createGroup: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            var collection = this.model.get('groups');
            collection.add([{
                name: collection.getNextDefaultGroupName(),
                order: collection.nextOrder()
            }]);
        },

        setName: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'name', this.$('.collection-name-input').val(),
                { silent: true }
            );
        },

        setDescription: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set(
                'description',
                this.$('.group-configuration-description-input').val(),
                { silent: true }
            );
        },

        setValues: function() {
            this.setName();
            this.setDescription();

            _.each(this.$('.groups li'), function(li, i) {
                var group = this.model.get('groups').at(i);

                if (group) {
                    group.set({
                        'name': $('.group-name', li).val()
                    });
                }
            }, this);

            return this;
        }
    });

    return GroupConfigurationEditorView;
});
