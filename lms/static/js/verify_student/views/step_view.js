/* global jQuery, _, Backbone, gettext */

/**
 * Base view for defining steps in the payment/verification flow.
 *
 * Step subclasses are responsible for defining a template
 * and installing custom event handlers (including buttons
 * to move to the next step).
 *
 */
var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.StepView = Backbone.View.extend({

        initialize: function(obj) {
            _.extend(this, obj);

            /* Mix non-conflicting functions from underscore.string
             * (all but include, contains, and reverse) into the
             * Underscore namespace.
             */
            _.mixin(_.str.exports());
        },

        render: function() {
            var templateHtml = $('#' + this.templateName + '-tpl').html();

            // Allow subclasses to add additional information
            // to the template context, perhaps asynchronously.
            this.updateContext(this.templateContext()).done(
                function(templateContext) {
                    // Render the template into the DOM
                    edx.HtmlUtils.setHtml($(this.el), edx.HtmlUtils.template(templateHtml)(templateContext));

                    // Allow subclasses to install custom event handlers
                    this.postRender();
                }
            ).fail(_.bind(this.handleError, this));

            return this;
        },

        handleError: function(errorTitle, errorMsg) {
            this.errorModel.set({
                errorTitle: errorTitle || gettext('Error'),
                errorMsg: errorMsg || gettext('An error has occurred. Please try reloading the page.'),
                shown: true
            });
        },

        templateContext: function() {
            var context = {
                nextStepTitle: this.nextStepTitle
            };
            return _.extend(context, this.defaultContext(), this.stepData);
        },

        /**
         * Provide default values for the template context.
         * Subclasses can use this to fill in values that
         * the underscore templates expect to be defined.
         * This is especially useful for testing, so that the
         * tests can pass in only the values relevant
         * to the test.
         */
        defaultContext: function() {
            return {};
        },

        /**
         * Subclasses can override this to add information to
         * the template context.  This returns an asynchronous
         * Promise, so the subclass can fill in the template
         * after completing an AJAX request.
         * The default implementation is a no-op.
         */
        updateContext: function(templateContext) {
            var view = this;
            return $.Deferred(
                function(defer) {
                    defer.resolveWith(view, [templateContext]);
                }
            ).promise();
        },

        postRender: function() {
            // Sub-classes can override this method
            // to install custom event handlers.
        },

        nextStep: function() {
            this.trigger('next-step');
        },

        goToStep: function(stepName) {
            this.trigger('go-to-step', stepName);
        }

    });
}(jQuery, _, Backbone, gettext));
