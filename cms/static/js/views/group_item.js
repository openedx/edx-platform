define([
    'js/views/list_item', 'js/views/group_item_edit', 'js/views/group_details'
], function(ListItem, GroupItemEdit, GroupDetails) {
    'use strict';

    var GroupItem = ListItem.extend({
        tagName: 'section', // TODO: confirm class and tag

        className: 'group-configuration group-configurations-list-item',

        createEditView: function() {
            return new GroupItemEdit({model: this.model});
        },

        createDetailsView: function() {
            return new GroupDetails({model: this.model});
        }
    });

    return GroupItem;
});
