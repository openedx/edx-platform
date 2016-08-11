(function(define, undefined) {
    'use strict';
    define([
        'jquery',
        'underscore',
        'backbone',
        'edx-ui-toolkit/js/utils/html-utils',
        'js/edxnotes/models/tab'
    ], function($, _, Backbone, HtmlUtils, TabModel) {
        var TabView = Backbone.View.extend({
            PanelConstructor: null,

            tabInfo: {
                name: '',
                class_name: ''
            },

            initialize: function(options) {
                _.bindAll(this, 'showLoadingIndicator', 'hideLoadingIndicator');
                this.options = _.defaults(options || {}, {
                    createTabOnInitialization: true,
                    createHeaderFooter: true
                });

                if (this.options.createTabOnInitialization) {
                    this.createTab();
                }
            },

        /**
         * Creates a tab for the view.
         */
            createTab: function() {
                this.tabModel = new TabModel(this.tabInfo);
                this.options.tabsCollection.add(this.tabModel);
                this.listenTo(this.tabModel, {
                    'change:is_active': function(model, value) {
                        if (value) {
                            this.render();
                        } else {
                            this.destroySubView();
                        }
                    },
                    'destroy': function() {
                        this.destroySubView();
                        this.tabModel = null;
                        this.onClose();
                    }
                });
            },

        /**
         * Renders content for the view.
         */
            render: function() {
                this.hideErrorMessage().showLoadingIndicator();
            // If the view is already rendered, destroy it.
                this.destroySubView();
                this.renderContent().always(this.hideLoadingIndicator);
                this.$('.sr-is-focusable.sr-tab-panel').focus();
                return this;
            },

            renderContent: function() {
                this.contentView = this.getSubView();
                this.$('.wrapper-tabs').append(this.contentView.render().$el);
                return $.Deferred().resolve().promise();
            },

            getSubView: function() {
                var collection = this.getCollection();
                return new this.PanelConstructor(
                    {
                        collection: collection,
                        scrollToTag: this.options.scrollToTag,
                        createHeaderFooter: this.options.createHeaderFooter
                    }
            );
            },

            destroySubView: function() {
                if (this.contentView) {
                    this.contentView.remove();
                    this.contentView = null;
                }
            },

        /**
         * Returns collection for the view.
         * @return {Backbone.Collection}
         */
            getCollection: function() {
                return this.collection;
            },

        /**
         * Callback that is called on closing the tab.
         */
            onClose: function() { },

        /**
         * Returns the page's loading indicator.
         */
            getLoadingIndicator: function() {
                return this.$('.ui-loading');
            },

        /**
         * Shows the page's loading indicator.
         */
            showLoadingIndicator: function() {
                this.getLoadingIndicator().removeClass('is-hidden');
                return this;
            },

        /**
         * Hides the page's loading indicator.
         */
            hideLoadingIndicator: function() {
                this.getLoadingIndicator().addClass('is-hidden');
                return this;
            },


        /**
         * Shows error message.
         */
            showErrorMessageHtml: function(htmlMessage) {
                var $wrapper = this.$('.wrapper-msg');
                $wrapper.removeClass('is-hidden');

                HtmlUtils.setHtml($wrapper.find('.msg-content .copy'), htmlMessage);
                return this;
            },

        /**
         * Hides error message.
         */
            hideErrorMessage: function() {
                this.$('.wrapper-msg')
                .addClass('is-hidden')
                .find('.msg-content .copy').html('');

                return this;
            }
        });

        return TabView;
    });
}).call(this, define || RequireJS.define);
