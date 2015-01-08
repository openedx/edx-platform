define([
    'js/views/list', 'js/views/group_item', 'gettext'
], function(ListView, GroupItemView, gettext) {
    'use strict';

    var GroupList = ListView.extend({
        tagName: 'div',

        className: 'group-configurations-list',

        emptyTemplateName: 'no-groups',

        // Translators: This refers to a content group that can be linked to a student cohort.
        itemCategoryDisplayName: gettext('content group'),

        createItemView: function(options) {
            return new GroupItemView(options);
        }
    });

    return GroupList;
});
