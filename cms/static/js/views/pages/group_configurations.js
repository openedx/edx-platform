define(['jquery', 'underscore', 'gettext', 'js/views/pages/base_page',
        'js/views/group_configurations_list'],
    function ($, _, gettext, BasePage, ConfigurationsListView) {
        'use strict';
        var GroupConfigurationsPage = BasePage.extend({
            initialize: function() {
                BasePage.prototype.initialize.call(this);
                this.listView = new ConfigurationsListView({
                    collection: this.collection
                });
            },

            renderPage: function() {
                this.$el.append(this.listView.render().el);
                this.addGlobalActions();
                return $.Deferred().resolve().promise();
            },

            addGlobalActions: function () {
                $(window).on('beforeunload', this.onBeforeUnload.bind(this));
            },

            onBeforeUnload: function () {
                var dirty = this.collection.find(function(configuration) {
                    return configuration.isDirty();
                });

                if(dirty) {
                    return gettext('You have unsaved changes. Do you really want to leave this page?');
                }
            }
        });

        return GroupConfigurationsPage;
    }); // end define();
