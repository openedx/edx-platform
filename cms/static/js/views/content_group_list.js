define([
    'js/views/list', 'js/views/content_group_item', 'gettext'
], function(ListView, GroupItemView, gettext) {
    'use strict';

    var ContentGroupList = ListView.extend({
        tagName: 'div',

        className: 'group-configurations-list',

        emptyTemplateName: 'no-content-groups',

        // Translators: This refers to a content group that can be linked to a student cohort.
        itemCategoryDisplayName: gettext('content group'),

        createItemView: function(options) {
            return new GroupItemView(options);
        }
    });

    return ContentGroupList;
});
