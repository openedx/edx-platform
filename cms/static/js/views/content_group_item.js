/**
 * This class defines an controller view for content groups.
 * It renders an editor view or a details view depending on the state
 * of the underlying model.
 * It is expected to be backed by a Group model.
 */
define([
    'js/views/list_item', 'js/views/content_group_editor', 'js/views/content_group_details'
], function(ListItemView, ContentGroupEditorView, ContentGroupDetailsView) {
    'use strict';

    var ContentGroupItemView = ListItemView.extend({
        tagName: 'section',

        baseClassName: 'content-group',

        createEditView: function() {
            return new ContentGroupEditorView({model: this.model});
        },

        createDetailsView: function() {
            return new ContentGroupDetailsView({model: this.model});
        }
    });

    return ContentGroupItemView;
});
