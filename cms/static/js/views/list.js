/**
 * A generic list view class.
 *
 * Expects the following properties to be overriden:
 * - emptyTemplateName (string): Name of an underscore template to
 *   render when the collection is empty.
 * - createItemView (function): Create and return an item view for a
 *   model in the collection.
 * - newModelOptions (object): Options to pass to models which are
 *   added to the collection.
 * - itemCategoryDisplayName (string): Display name for the category
 *   of items this list contains.  For example, 'Group Configuration'.
 *   Note that it must be translated.
 */
define([
    'js/views/baseview'
], function(BaseView) {
    'use strict';
    var List = BaseView.extend({
        events: {
            'click .action-add': 'addOne'
        },

        initialize: function() {
            this.emptyTemplate = this.loadTemplate(this.emptyTemplateName);
            this.listenTo(this.collection, 'add', this.addNewItemView);
            this.listenTo(this.collection, 'remove', this.handleDestory);
            this.template = this.loadTemplate('add-list-item');
            // Don't render the add button when editing a form
            this.listenTo(this.collection, 'change:editing', this.toggleAddButton);
            this.listenTo(this.collection, 'add', this.toggleAddButton);
            this.listenTo(this.collection, 'remove', this.renderAddButton);
        },

        render: function() {
            if (this.collection.length === 0) {
                this.$el.html(this.emptyTemplate());
            } else {
                var frag = document.createDocumentFragment();

                this.collection.each(function(model) {
                    frag.appendChild(this.createItemView({model: model}).render().el);
                }, this);

                this.$el.html([frag]);
                this.renderAddButton();
            }

            return this;
        },

        removeAddButton: function() {
            var addItemElement = this.$('.action-add');
            if (addItemElement.length) {
                addItemElement.remove();
            }
        },

        renderAddButton: function() {
            this.removeAddButton();
            if (this.collection.length) {
                this.$el.append(this.template({
                    itemCategory: this.itemCategory,
                    itemCategoryDisplayName: this.itemCategoryDisplayName
                }));
            }
        },

        toggleAddButton: function(model) {
            if (model.get('editing')) {
                this.removeAddButton();
            } else {
                this.renderAddButton();
            }
        },

        addNewItemView: function (model) {
            var view = this.createItemView({model: model});

            // If items already exist, just append one new. Otherwise, overwrite
            // no-content message.
            if (this.collection.length > 1) {
                this.$el.append(view.render().el);
            } else {
                this.$el.html(view.render().el);
            }

            view.$el.focus();
        },

        addOne: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.collection.add({editing: true}, this.newModelOptions);
        },

        handleDestory: function () {
            if (this.collection.length === 0) {
                this.$el.html(this.emptyTemplate());
            }
        }
    });

    return List;
});
