/**
 * Base view for defining steps in the payment/verification flow.
 *
 * Each step view lazy-loads its underscore template.
 * This reduces the size of the initial page, since we don't
 * need to include the DOM structure for each step
 * in the initial load.
 *
 * Step subclasses are responsible for defining a template
 * and installing custom event handlers (including buttons
 * to move to the next step).
 *
 * The superclass is responsible for downloading the underscore
 * template and rendering it, using context received from
 * the server (in data attributes on the initial page load).
 *
 */
 var edx = edx || {};

 (function( $, _, _s, Backbone, gettext ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.StepView = Backbone.View.extend({

        initialize: function( obj ) {
            _.extend( this, obj );

            /* Mix non-conflicting functions from underscore.string
             * (all but include, contains, and reverse) into the
             * Underscore namespace
             */
            _.mixin( _s.exports() );
        },

        render: function() {
            if ( !this.renderedHtml && this.templateUrl) {
                $.ajax({
                    url: this.templateUrl,
                    type: 'GET',
                    context: this,
                    success: this.handleResponse,
                    error: this.handleError
                });
            } else {
                $( this.el ).html( this.renderedHtml );
                this.postRender();
            }
        },

        handleResponse: function( data ) {
            var context = {
                nextStepNum: this.nextStepNum,
                nextStepTitle: this.nextStepTitle
            };

            // Include step-specific information
            _.extend( context, this.stepData );

            this.renderedHtml = _.template( data, context );
            $( this.el ).html( this.renderedHtml );

            this.postRender();
        },

        handleError: function() {
            this.errorModel.set({
                errorTitle: gettext("Error"),
                errorMsg: gettext("An unexpected error occurred.  Please reload the page to try again."),
                shown: true
            });
        },

        postRender: function() {
            // Sub-classes can override this method
            // to install custom event handlers.
        },

        nextStep: function() {
            this.trigger('next-step');
        },

        goToStep: function( stepName ) {
            this.trigger( 'go-to-step', stepName );
        }

    });

 })( jQuery, _, _.str, Backbone, gettext );
