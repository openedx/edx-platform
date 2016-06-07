/**
 * A generic list view class.
 *
 * Expects the following properties to be overriden:
 *   render when the collection is empty.
 * - createItemView (function): Create and return an item view for a
 *   model in the collection.
 * - newModelOptions (object): Options to pass to models which are
 *   added to the collection.
 * - itemCategoryDisplayName (string): Display name for the category
 *   of items this list contains.  For example, 'Group Configuration'.
 *   Note that it must be translated.
 * - emptyMessage (string): Text to render when the list is empty.
 */
define([
    'js/views/baseview'
], function(BaseView) {
    'use strict';
    var ListView = BaseView.extend({
        events: {
            'click .action-add': 'onAddItem',
            'click .new-button': 'onAddItem'
        },

        listContainerCss: '.list-items',

        initialize: function() {
            this.listenTo(this.collection, 'add', this.addNewItemView);
            this.listenTo(this.collection, 'remove', this.onRemoveItem);
            this.template = this.loadTemplate('list');

            // Don't render the add button when editing a form
            this.listenTo(this.collection, 'change:editing', this.toggleAddButton);
            this.listenTo(this.collection, 'add', this.toggleAddButton);
            this.listenTo(this.collection, 'remove', this.toggleAddButton);
        },

        render: function(model) {
            this.$el.html(this.template({
                itemCategoryDisplayName: this.itemCategoryDisplayName,
                newItemMessage: this.newItemMessage,
                emptyMessage: this.emptyMessage,
                length: this.collection.length,
                isEditing: model && model.get('editing'),
                canCreateNewItem: this.canCreateItem(this.collection)
            }));

            this.collection.each(function(model) {
                this.$(this.listContainerCss).append(this.createItemView({model: model}).render().el);
            }, this);

            return this;
        },

        hideOrShowAddButton: function(shouldShow) {
            var addButtonCss = '.action-add';
            if (this.collection.length) {
                if (shouldShow) {
                    this.$(addButtonCss).removeClass('is-hidden');
                } else {
                    this.$(addButtonCss).addClass('is-hidden');
                }
            }
        },

        toggleAddButton: function(model) {
            if (model.get('editing') && this.collection.contains(model)) {
                this.hideOrShowAddButton(false);
            } else {
                this.hideOrShowAddButton(true);
            }
        },

        addNewItemView: function (model) {
            var view = this.createItemView({model: model});

            // If items already exist, just append one new.
            // Otherwise re-render the empty list HTML.
            if (this.collection.length > 1) {
                this.$(this.listContainerCss).append(view.render().el);
            } else {
                this.render();
            }

            view.$el.focus();
        },

        canCreateItem: function(collection) {
            var canCreateNewItem = true;
            if (collection.length > 0) {
                var maxAllowed = collection.maxAllowed;
                if (!_.isUndefined(maxAllowed) && collection.length >= maxAllowed) {
                    canCreateNewItem = false;
                }
            }
            return canCreateNewItem;
        },

        onAddItem: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.collection.add({editing: true}, this.newModelOptions);
        },

        onRemoveItem: function () {
            if (this.collection.length === 0) {
                this.render();
            }
        }
    });

    return ListView;
});
