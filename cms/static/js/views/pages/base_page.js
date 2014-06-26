/**
 * This is the base view that all Studio pages extend from.
 */
define(["jquery", "underscore", "gettext", "js/views/baseview"],
    function ($, _, gettext, BaseView) {
        var BasePage = BaseView.extend({

            initialize: function() {
                BaseView.prototype.initialize.call(this);
            },

            hasContent: function() {
                return true;
            },

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
