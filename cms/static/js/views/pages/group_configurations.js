define([
    'jquery', 'underscore', 'gettext', 'js/views/pages/base_page',
    'js/views/group_configurations_list', 'js/views/partition_group_list'
],
function($, _, gettext, BasePage, GroupConfigurationsListView, PartitionGroupListView) {
    'use strict';
    var GroupConfigurationsPage = BasePage.extend({
        initialize: function(options) {
            var currentScheme,
                i;

            BasePage.prototype.initialize.call(this);
            this.experimentsEnabled = options.experimentsEnabled;
            if (this.experimentsEnabled) {
                this.experimentGroupConfigurations = options.experimentGroupConfigurations;
                this.experimentGroupsListView = new GroupConfigurationsListView({
                    collection: this.experimentGroupConfigurations
                });
            }

            this.allGroupConfigurations = options.allGroupConfigurations || [];
            this.allGroupViewList = [];
            for (i = 0; i < this.allGroupConfigurations.length; i++) {
                currentScheme = this.allGroupConfigurations[i].get('scheme');
                this.allGroupViewList.push(
                    new PartitionGroupListView({
                        collection: this.allGroupConfigurations[i].get('groups'),
                        restrictEditing: this.allGroupConfigurations[i].get('read_only'),
                        scheme: currentScheme
                    })
                );
            }
        },

        renderPage: function() {
            var hash = this.getLocationHash(),
                i,
                currentClass;
            if (this.experimentsEnabled) {
                this.$('.wrapper-groups.experiment-groups').append(this.experimentGroupsListView.render().el);
            }

            // Render the remaining Configuration groups
            for (i = 0; i < this.allGroupViewList.length; i++) {
                currentClass = '.wrapper-groups.content-groups.' + this.allGroupViewList[i].scheme;
                this.$(currentClass).append(this.allGroupViewList[i].render().el);
            }

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

        /**
         * Checks the Partition Group Configurations to see if the isDirty bit is set
         * @returns {boolean} True if any partition group has the dirty bit set.
         */
        areAnyConfigurationsDirty: function() {
            var i;
            for (i = 0; i < this.allGroupConfigurations.length; i++) {
                if (this.allGroupConfigurations[i].isDirty()) {
                    return true;
                }
            }
            return false;
        },

        onBeforeUnload: function() {
            var dirty = this.areAnyConfigurationsDirty() ||
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
