/**
 * This class defines an controller view for content experiment group configurations.
 * It renders an editor view or a details view depending on the state
 * of the underlying model.
 * It is expected to be backed by a Group model.
 */
define([
    'js/views/list_item', 'js/views/group_configuration_details', 'js/views/group_configuration_editor', 'gettext'
], function(
    ListItemView, GroupConfigurationDetailsView, GroupConfigurationEditorView, gettext
) {
    'use strict';

    var GroupConfigurationItemView = ListItemView.extend({
        events: {
            'click .delete': 'deleteItem'
        },

        tagName: 'section',

        baseClassName: 'group-configuration',

        canDelete: true,

        // Translators: this refers to a collection of groups.
        itemDisplayName: gettext('group configuration'),

        attributes: function() {
            return {
                id: this.model.get('id'),
                tabindex: -1
            };
        },

        createEditView: function() {
            return new GroupConfigurationEditorView({model: this.model});
        },

        createDetailsView: function() {
            return new GroupConfigurationDetailsView({model: this.model});
        }
    });

    return GroupConfigurationItemView;
});
