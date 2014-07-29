define([
    'jquery', 'underscore', 'gettext', 'js/views/baseview',
    'js/views/group_configurations_list', 'tooltip_manager'
],
function ($, _, gettext, BaseView, GroupConfigurationsList) {
    'use strict';
    var GroupConfigurationsPage = BaseView.extend({
        initialize: function() {
            BaseView.prototype.initialize.call(this);
            this.listView = new GroupConfigurationsList({
                collection: this.collection
            });
        },

        render: function() {
            this.hideLoadingIndicator();
            this.$('.content-primary').append(this.listView.render().el);
            this.addButtonActions();
            this.addWindowActions();
        },

        addButtonActions: function () {
            this.$('.nav-actions .new-button').click(function (event) {
                this.listView.addOne(event);
            }.bind(this));
        },

        addWindowActions: function () {
            $(window).on('beforeunload', this.onBeforeUnload.bind(this));
        },

        onBeforeUnload: function () {
            var dirty = this.collection.find(function(configuration) {
                return configuration.isDirty();
            });

            if(dirty) {
                return gettext(
                    'You have unsaved changes. Do you really want to leave this page?'
                );
            }
        }
    });

    return GroupConfigurationsPage;
}); // end define();
