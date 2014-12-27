define([
    'js/views/list_item_edit', 'jquery'
],
function(ListItemEdit, $) {
    'use strict';

    var GroupItemEdit = ListItemEdit.extend({
        tagName: 'div',
        className: 'group-configuration-details',
        events: {
            'submit': 'setAndClose',
            'click .action-cancel': 'cancel'
        },

        initialize: function() {
            ListItemEdit.prototype.initialize.call(this);
            this.template = this.loadTemplate('group-item-edit');
        },

        getTemplateOptions: function() {
            return {
                name: this.model.escape('name'),
                index: this.model.collection.indexOf(this.model),
                isNew: this.model.isNew()
            };
        },

        setValues: function() {
            this.model.set({name: this.$('input').val()});
            return this;
        },

        getSaveableModel: function() {
            return this.model.collection.parents[0];
        }
    });

    return GroupItemEdit;
});
