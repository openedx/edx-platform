define([
    'jquery', 'underscore', 'gettext', 'js/views/pages/base_page',
    'js/views/group_configurations_list', 'js/views/group_list'
],
function ($, _, gettext, BasePage, GroupConfigurationsList, GroupList) {
    'use strict';
    var GroupConfigurationsPage = BasePage.extend({
        events: function() {
            var events = {
                'click .cohort-groups .new-button': this.cohortGroupsListView.addOne.bind(this.cohortGroupsListView)
            };
            if (this.experimentsEnabled) {
                events['click .experiment-groups .new-button'] = this.experimentGroupsListView.addOne.bind(this.experimentGroupsListView);
            }
            return events;
        },

        initialize: function(options) {
            BasePage.prototype.initialize.call(this);
            this.experimentsEnabled = options.experimentsEnabled;
            if (this.experimentsEnabled) {
                this.experimentGroupsCollection = options.experimentGroupsCollection;
                this.experimentGroupsListView = new GroupConfigurationsList({
                    collection: this.experimentGroupsCollection
                });
            }
            this.cohortGroupConfiguration = options.cohortGroupConfiguration;
            this.cohortGroupsListView = new GroupList({
                collection: this.cohortGroupConfiguration.get('groups')
            });
        },

        renderPage: function() {
            var hash = this.getLocationHash();
            if (this.experimentsEnabled) {
                this.$('.experiment-groups').append(this.experimentGroupsListView.render().el);
            }
            this.$('.cohort-groups').append(this.cohortGroupsListView.render().el);
            this.addWindowActions();
            if (hash) {
                // Strip leading '#' to get id string to match
                this.expandConfiguration(hash.replace('#', ''));
            }
            return $.Deferred().resolve().promise();
        },

        addWindowActions: function () {
            $(window).on('beforeunload', this.onBeforeUnload.bind(this));
        },

        onBeforeUnload: function () {
            var dirty = this.cohortGroupConfiguration.isDirty ||
                (this.experimentsEnabled && this.experimentGroupsCollection.find(function(configuration) {
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
        expandConfiguration: function (id) {
            var groupConfig = this.experimentsEnabled && this.experimentGroupsCollection.findWhere({
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
