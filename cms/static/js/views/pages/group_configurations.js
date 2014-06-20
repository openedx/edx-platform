define([
    'jquery', 'underscore', 'gettext', 'js/views/baseview',
    'js/views/group_configurations_list'
],
function ($, _, gettext, BaseView, ConfigurationsListView) {
    'use strict';
    var GroupConfigurationsPage = BaseView.extend({
        initialize: function() {
            BaseView.prototype.initialize.call(this);
            this.listView = new ConfigurationsListView({
                collection: this.collection
            });
        },

        render: function() {
            this.hideLoadingIndicator();
            this.$el.append(this.listView.render().el);
            this.addGlobalActions();
        },

        addGlobalActions: function () {
            $(window).on('beforeunload', this.onBeforeUnload.bind(this));
        },

        onBeforeUnload: function () {
            var dirty = this.collection.find(function(configuration) {
                return configuration.isDirty();
            });

            if(dirty) {
                return gettext(
                    'You have unsaved changes. Do you really want to ' +
                    'leave this page?'
                );
            }
        }
    });

    return GroupConfigurationsPage;
}); // end define();
