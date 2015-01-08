define([
    'js/views/list_item', 'js/views/content_group_edit', 'js/views/content_group_details'
], function(ListItem, GroupItemEdit, GroupDetails) {
    'use strict';

    var ContentGroupItem = ListItem.extend({
        tagName: 'section', // TODO: confirm class and tag

        createEditView: function() {
            return new GroupItemEdit({model: this.model});
        },

        createDetailsView: function() {
            return new GroupDetails({model: this.model});
        }
    });

    return ContentGroupItem;
});
