define([
    'js/views/list', 'js/views/group_item', 'gettext'
], function(ListView, GroupItemView, gettext) {
    'use strict';

    var GroupList = ListView.extend({
        tagName: 'div',

        className: 'group-configurations-list',

        emptyTemplateName: 'no-groups',

        // Translators: This refers to a group which allows cohoroted
        // students to access specific content.
        itemCategoryDisplayName: gettext('cohorted content group'),

        createItemView: function(options) {
            return new GroupItemView(options);
        }
    });

    return GroupList;
});
