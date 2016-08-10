define([
    'jquery', 'underscore', 'gettext', 'js/views/pages/base_page',
    'js/views/group_configurations_list', 'js/views/content_group_list'
],
function($, _, gettext, BasePage, GroupConfigurationsListView, ContentGroupListView) {
    'use strict';
    var GroupConfigurationsPage = BasePage.extend({
        initialize: function(options) {
            BasePage.prototype.initialize.call(this);
            this.experimentsEnabled = options.experimentsEnabled;
            if (this.experimentsEnabled) {
                this.experimentGroupConfigurations = options.experimentGroupConfigurations;
                this.experimentGroupsListView = new GroupConfigurationsListView({
                    collection: this.experimentGroupConfigurations
                });
            }
            this.contentGroupConfiguration = options.contentGroupConfiguration;
            this.cohortGroupsListView = new ContentGroupListView({
                collection: this.contentGroupConfiguration.get('groups')
            });
        },

        renderPage: function() {
            var hash = this.getLocationHash();
            if (this.experimentsEnabled) {
                this.$('.wrapper-groups.experiment-groups').append(this.experimentGroupsListView.render().el);
            }
            this.$('.wrapper-groups.content-groups').append(this.cohortGroupsListView.render().el);
            this.addWindowActions();
            if (hash) {
                // Strip leading '#' to get id string to match
                this.expandConfiguration(hash.replace('#', ''));
            }
            return $.Deferred().resolve().promise();
        },

        addWindowActions: function() {
            $(window).on('beforeunload', this.onBeforeUnload.bind(this));
        },

        onBeforeUnload: function() {
            var dirty = this.contentGroupConfiguration.isDirty() ||
                (this.experimentsEnabled && this.experimentGroupConfigurations.find(function(configuration) {
                    return configuration.isDirty();
                }));

            if (dirty) {
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
        expandConfiguration: function(id) {
            var groupConfig = this.experimentsEnabled && this.experimentGroupConfigurations.findWhere({
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
