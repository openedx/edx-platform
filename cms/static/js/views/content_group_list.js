/**
 * This class defines a list view for content groups.
 * It is expected to be backed by a Group collection.
 */
define([
    'js/views/list', 'js/views/content_group_item', 'gettext'
], function(ListView, ContentGroupItemView, gettext) {
    'use strict';

    var ContentGroupListView = ListView.extend({
        tagName: 'div',

        className: 'group-configurations-list',

        emptyTemplateName: 'no-content-groups',

        // Translators: This refers to a content group that can be linked to a student cohort.
        itemCategoryDisplayName: gettext('content group'),

        createItemView: function(options) {
            return new ContentGroupItemView(options);
        },

        /* The Group collection is sorted alphabetically, but newly
         * created content groups are appended to the bottom of the
         * list.  Disable sorting when adding new models to keep the
         * list item's index in sync with its position on screen.
         */
        newModelOptions: {sort: false}
    });

    return ContentGroupListView;
});
