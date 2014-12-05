/**
 * Base view for the payment/verification flow.
 *
 * This view is responsible for the "progress steps"
 * at the top of the page, but it delegates
 * to subviews to render individual steps.
 *
 */
var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.PayAndVerifyView = Backbone.View.extend({
        el: '#pay-and-verify-container',

        template: '#progress-tpl',

        subviews: {},

        initialize: function( obj ) {
            var i,
                stepName,
                stepData,
                subview,
                nextStepTitle,
                subviewConstructors;

            this.displaySteps = obj.displaySteps || [];

            // Determine which step we're starting on
            // Depending on how the user enters the flow,
            // this could be anywhere in the sequence of steps.
            this.currentStepIndex = _.indexOf(
                _.pluck( this.displaySteps, 'name' ),
                obj.currentStep
            );

            // We need to initialize this here, because
            // outside of this method the subview classes
            // might not yet have been loaded.
            subviewConstructors = {
                'intro-step': edx.verify_student.IntroStepView,
                'make-payment-step': edx.verify_student.MakePaymentStepView,
                'payment-confirmation-step': edx.verify_student.PaymentConfirmationStepView,
                'face-photo-step': edx.verify_student.FacePhotoStepView,
                'id-photo-step': edx.verify_student.IDPhotoStepView,
                'review-photos-step': edx.verify_student.ReviewPhotosStepView,
                'enrollment-confirmation-step': edx.verify_student.EnrollmentConfirmationStepView
            };

            for ( i = 0; i < this.displaySteps.length; i++ ) {
                stepName = this.displaySteps[i].name;
                subview = null;

                if ( i < this.displaySteps.length - 1) {
                    nextStepTitle = this.displaySteps[i + 1].title;
                }
                else {
                    nextStepTitle = "";
                }

                if ( subviewConstructors.hasOwnProperty( stepName ) ) {
                    stepData = {};

                    // Add any info specific to this step
                    if ( obj.stepInfo.hasOwnProperty( stepName ) ) {
                        _.extend( stepData, obj.stepInfo[ stepName ] );
                    }

                    // Create the subview instance
                    // Note that we are NOT yet rendering the view,
                    // so this doesn't trigger GET requests or modify
                    // the DOM.
                    this.subviews[stepName] = new subviewConstructors[stepName]({
                        templateUrl: this.displaySteps[i].templateUrl,
                        nextStepNum: (i + 2), // Next index, starting from 1
                        nextStepTitle: nextStepTitle,
                        stepData: stepData
                    });

                    // Listen for next step events
                    this.listenTo(this.subviews[stepName], 'next-step', this.nextStep);
                }
            }
        },

        render: function() {
            this.renderProgress();
            this.renderCurrentStep();
            return this;
        },

        renderProgress: function() {
            var renderedHtml, context;

            context = {
                steps: this.steps()
            };

            renderedHtml = _.template( $(this.template).html(), context );
            $(this.el).html(renderedHtml);
        },

        renderCurrentStep: function() {
            var stepName, stepView, stepEl;

            // Get or create the step container
            stepEl = $("#current-step-container");
            if (!stepEl.length) {
                stepEl = $('<div id="current-step-container"></div>').appendTo(this.el);
            }

            // Render the subview
            // Note that this will trigger a GET request for the
            // underscore template.
            // When the view is rendered, it will overwrite the existing
            // step in the DOM.
            stepName = this.displaySteps[ this.currentStepIndex ].name;
            stepView = this.subviews[ stepName ];
            stepView.el = stepEl;
            stepView.render();
        },

        nextStep: function() {
            this.currentStepIndex = Math.min( this.currentStepIndex + 1, this.displaySteps.length - 1 );
            this.render();
        },

        steps: function() {
            var i,
                stepDescription,
                steps = [];

            for ( i = 0; i < this.displaySteps.length; i++ ) {
                stepDescription = {
                    title: this.displaySteps[i].title,
                    isCurrent: (i === this.currentStepIndex ),
                    isComplete: (i < this.currentStepIndex )
                };
                steps.push(stepDescription);
            }

            return steps;
        }
    });

})(jQuery, _, Backbone, gettext);
