/**
 * This class defines an controller view for partition groups.
 * It renders an editor view or a details view depending on the state
 * of the underlying model.
 * It is expected to be backed by a Group model.
 */
define([
    'js/views/list_item', 'js/views/content_group_editor', 'js/views/partition_group_details',
    'gettext', 'common/js/components/utils/view_utils'
], function(ListItemView, ContentGroupEditorView, PartitionGroupDetailsView, gettext) {
    'use strict';

    var PartitionGroupItemView = ListItemView.extend({
        events: {
            'click .delete': 'deleteItem'
        },

        tagName: 'section',

        baseClassName: 'partition-group',

        canDelete: true,

        itemDisplayName: gettext('content group'),

        attributes: function() {
            return {
                id: this.model.get('id'),
                tabindex: -1
            };
        },

        createEditView: function() {
            return new ContentGroupEditorView({model: this.model});
        },

        createDetailsView: function() {
            return new PartitionGroupDetailsView({model: this.model,
                restrictEditing: this.options.restrictEditing
            });
        }
    });

    return PartitionGroupItemView;
});
