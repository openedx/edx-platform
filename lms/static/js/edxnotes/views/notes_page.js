;(function (define, undefined) {
    'use strict';
    define([
        'backbone', 'js/edxnotes/views/recent_activity_view'
    ], function (Backbone, RecentActivityView) {
        var NotesPageView = Backbone.View.extend({
            initialize: function (options) {
                this.options = options;
            },

            render: function () {
                this.view = new RecentActivityView({
                    collection: this.collection
                }).render();

                this.$('.course-info').append(this.view.$el);
                this.hideLoadingIndicator();

                return this;
            },

            /**
             * Show the page's loading indicator.
             */
            showLoadingIndicator: function() {
                this.$('.ui-loading').removeClass('is-hidden');
            },

            /**
             * Hide the page's loading indicator.
             */
            hideLoadingIndicator: function() {
                this.$('.ui-loading').addClass('is-hidden');
            }
        });

        return NotesPageView;
    });
}).call(this, define || RequireJS.define);
