define(['jquery', 'underscore', 'gettext', 'js/views/pages/base_page',
        'js/views/group_configurations_list'],
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
                this.$el.append(this.listView.render().el);
                this.addButtonActions();
                this.addWindowActions();
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
            }
        });

        return GroupConfigurationsPage;
    }); // end define();
