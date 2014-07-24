define([
    'js/views/baseview', 'jquery', 'js/views/group_configuration_item'
], function(
    BaseView, $, GroupConfigurationItemView
) {
    'use strict';
    var GroupConfigurationsList = BaseView.extend({
        tagName: 'div',
        className: 'group-configurations-list',
        events: {
            'click .new-button': 'addOne'
        },

        initialize: function() {
            this.emptyTemplate = this.loadTemplate('no-group-configurations');
            this.listenTo(this.collection, 'add', this.addNewItemView);
            this.listenTo(this.collection, 'remove', this.handleDestory);
        },

        render: function() {
            var configurations = this.collection;

            if(configurations.length === 0) {
                this.$el.html(this.emptyTemplate());
            } else {
                var frag = document.createDocumentFragment();

                configurations.each(function(configuration) {
                    var view = new GroupConfigurationItemView({
                        model: configuration
                    });

                    frag.appendChild(view.render().el);
                });

                this.$el.html([frag]);
            }

            return this;
        },

        addNewItemView: function (model) {
            var view = new GroupConfigurationItemView({
                model: model
            });

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
            if(event && event.preventDefault) { event.preventDefault(); }
            this.collection.add([{ editing: true }]);
        },

        handleDestory: function () {
            if(this.collection.length === 0) {
                this.$el.html(this.emptyTemplate());
            }
        }
    });

    return GroupConfigurationsList;
});
