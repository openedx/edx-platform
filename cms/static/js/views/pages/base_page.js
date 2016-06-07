/**
 * This is the base view that all Studio pages extend from.
 */
define(['jquery', 'js/views/baseview'],
    function ($, BaseView) {
        var BasePage = BaseView.extend({

            initialize: function() {
                BaseView.prototype.initialize.call(this);
            },

            /**
             * Returns true if this page is currently showing any content. If this returns false
             * then the page will unhide the div with the class 'no-content'.
             */
            hasContent: function() {
                return true;
            },

            /**
             * This renders the page's content and returns a promise that will be resolved once
             * the rendering has completed.
             * @returns {jQuery promise} A promise representing the rendering of the page.
             */
            renderPage: function() {
                return $.Deferred().resolve().promise();
            },

            /**
             * Renders the current page while showing a loading indicator. Note that subclasses
             * of BasePage should implement renderPage to perform the rendering of the content.
             * If the page has no content (i.e. it returns false for hasContent) then the
             * div with the class 'no-content' will be shown.
             */
            render: function() {
                var self = this;
                this.$('.ui-loading').removeClass('is-hidden');
                this.renderPage().done(function() {
                    if (!self.hasContent()) {
                        self.$('.no-content').removeClass('is-hidden');
                    }
                }).always(function() {
                    self.$('.ui-loading').addClass('is-hidden');
                });
                return this;
            }
        });

        return BasePage;
    }); // end define();
