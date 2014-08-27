define([
    'jquery', 'underscore', 'gettext', 'js/views/pages/base_page',
    'js/views/group_configurations_list'
],
function ($, _, gettext, BasePage, GroupConfigurationsList) {
    'use strict';
    var GroupConfigurationsPage = BasePage.extend({
        initialize: function() {
            BasePage.prototype.initialize.call(this);
            this.listView = new GroupConfigurationsList({
                collection: this.collection
            });
        },

        renderPage: function() {
            var hash = this.getLocationHash();
            this.$('.content-primary').append(this.listView.render().el);
            this.addButtonActions();
            this.addWindowActions();
            if (hash) {
                // Strip leading '#' to get id string to match
                this.expandConfiguration(hash.replace('#', ''));
            }
            return $.Deferred().resolve().promise();
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
                return gettext('You have unsaved changes. Do you really want to leave this page?');
            }
        },

        /**
         * Helper method that returns url hash.
         * @return {String} Returns anchor part of current url.
         */
        getLocationHash: function() {
            return window.location.hash;
        },

        /**
         * Focus on and expand group configuration with peculiar id.
         * @param {String|Number} Id of the group configuration.
         */
        expandConfiguration: function (id) {
            var groupConfig = this.collection.findWhere({
                id: parseInt(id)
            });

            if (groupConfig) {
                groupConfig.set('showGroups', true);
                this.$('#' + id).focus();
            }
        }
    });

    return GroupConfigurationsPage;
}); // end define();
