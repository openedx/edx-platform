/**
 * Base view for defining steps in the payment/verification flow.
 *
 * Step subclasses are responsible for defining a template
 * and installing custom event handlers (including buttons
 * to move to the next step).
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
            var templateHtml = $( "#" + this.templateName + "-tpl" ).html(),
                templateContext = {
                    nextStepNum: this.nextStepNum,
                    nextStepTitle: this.nextStepTitle
                };

            // Include step-specific information from the server
            // (passed in from data- attributes to the parent view)
            _.extend( templateContext, this.stepData );

            // Allow subclasses to add additional information
            // to the template context, perhaps asynchronously.
            this.updateContext( templateContext ).done(
                function( templateContext ) {
                    // Render the template into the DOM
                    $( this.el ).html( _.template( templateHtml, templateContext ) );

                    // Allow subclasses to install custom event handlers
                    this.postRender();
                }
            ).fail( _.bind( this.handleError, this ) );
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
                errorTitle: gettext( "Error" ),
                errorMsg: gettext( "An unexpected error occurred.  Please reload the page to try again." ),
                shown: true
            });
        },

        /**
         * Subclasses can override this to add information to
         * the template context.  This returns an asynchronous
         * Promise, so the subclass can fill in the template
         * after completing an AJAX request.
         * The default implementation is a no-op.
         */
        updateContext: function( templateContext ) {
            var view = this;
            return $.Deferred(
                function( defer ) {
                    defer.resolveWith( view, [ templateContext ]);
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

        goToStep: function( stepName ) {
            this.trigger( 'go-to-step', stepName );
        }

    });

 })( jQuery, _, _.str, Backbone, gettext );
