define([
    'js/views/list_item', 'js/views/group_configuration_details', 'js/views/group_configuration_edit'
], function(
    ListItem, GroupConfigurationDetails, GroupConfigurationEdit
) {
    'use strict';

    var GroupConfigurationsItem = ListItem.extend({
        events: {
            'click .delete': 'deleteItem'
        },

        tagName: 'section',

        attributes: function () {
            return {
                'id': this.model.get('id'),
                'tabindex': -1
            };
        },

        className: function () {
            var index = this.model.collection.indexOf(this.model);

            return [
                'group-configuration',
                'group-configurations-list-item',
                'group-configurations-list-item-' + index
            ].join(' ');
        },

        itemDisplayName: 'Group Configuration',

        canDelete: true,

        createEditView: function() {
            return new GroupConfigurationEdit({model: this.model});
        },

        createDetailsView: function() {
            return new GroupConfigurationDetails({model: this.model});
        }
    });

    return GroupConfigurationsItem;
});
