;(function (define, undefined) {
'use strict';
define([
    'underscore', 'backbone', 'js/edxnotes/models/tab'
], function (_, Backbone, TabModel) {
    var TabView = Backbone.View.extend({
        SubViewConstructor: null,

        tabInfo: {
            name: '',
            class_name: ''
        },

        initialize: function (options) {
            _.bindAll(this, 'showLoadingIndicator', 'hideLoadingIndicator');
            this.options = _.defaults(options || {}, {
                createTabOnInitialization: true
            });

            if (this.options.createTabOnInitialization) {
                this.createTab();
            }
        },

        /**
         * Creates a tab for the view.
         */
        createTab: function () {
            this.tabModel = new TabModel(this.tabInfo);
            this.options.tabsCollection.add(this.tabModel);
            this.tabModel.on({
                'change:is_active': function (model, value) {
                    if (value) {
                        this.render();
                    } else {
                        this.destroySubView();
                    }
                },
                'destroy': function () {
                    this.destroySubView();
                    this.tabModel = null;
                    this.onClose();
                }
            }, this);
        },

        /**
         * Renders content for the view.
         */
        render: function () {
            this.showLoadingIndicator();
            // If the view is already rendered, destroy it.
            this.destroySubView();
            this.renderContent().always(this.hideLoadingIndicator);
            return this;
        },

        renderContent: function () {
            var contentView = this.getSubView();
            this.$('.course-info').append(contentView.render().$el);
            return $.Deferred().resolve().promise();
        },

        getSubView: function () {
            var collection = this.getCollection();
            return new this.SubViewConstructor({collection: collection});
        },

        destroySubView: function () {
            this.$('.edx-notes-page-items-list').remove();
        },

        /**
         * Returns collection for the view.
         * @return {Backbone.Collection}
         */
        getCollection: function () {
            return this.collection;
        },

        /**
         * Callback that is called on closing the tab.
         */
        onClose: function () { },

        /**
         * Shows the page's loading indicator.
         */
        showLoadingIndicator: function() {
            this.$('.ui-loading').removeClass('is-hidden');
        },

        /**
         * Hides the page's loading indicator.
         */
        hideLoadingIndicator: function() {
            this.$('.ui-loading').addClass('is-hidden');
        },


        /**
         * Shows error message.
         */
        showErrorMessage: function (message) {
            this.$('.inline-error')
                .text(message)
                .removeClass('is-hidden');
        },

        /**
         * Hides error message.
         */
        hideErrorMessage: function () {
            this.$('.inline-error')
                .text('')
                .addClass('is-hidden');
        }
    });

    return TabView;
});
}).call(this, define || RequireJS.define);
