/**
 * Reverification flow.
 *
 * This flow allows students who have a denied or expired verification
 * to re-submit face and ID photos.  It re-uses most of the same sub-views
 * as the payment/verification flow.
 *
 */

 var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.ReverifyView = Backbone.View.extend({
        el: '#reverify-container',

        stepOrder: [
            "face-photo-step",
            "id-photo-step",
            "review-photos-step",
            "reverify-success-step"
        ],
        stepViews: {},

        initialize: function( obj ) {
            this.errorModel = obj.errorModel || null;
            this.initializeStepViews( obj.stepInfo || {} );
            this.currentStepIndex = 0;
        },

        initializeStepViews: function( stepInfo ) {
            var verificationModel, stepViewConstructors, nextStepTitles;

            // We need to initialize this here, because
            // outside of this method the subview classes
            // might not yet have been loaded.
            stepViewConstructors = {
                'face-photo-step': edx.verify_student.FacePhotoStepView,
                'id-photo-step': edx.verify_student.IDPhotoStepView,
                'review-photos-step': edx.verify_student.ReviewPhotosStepView,
                'reverify-success-step': edx.verify_student.ReverifySuccessStepView
            };

            nextStepTitles = [
                gettext( "Take a photo of your ID" ),
                gettext( "Review your info" ),
                gettext( "Confirm" ),
                ""
            ];

            // Create the verification model, which is shared
            // among the different steps.  This allows
            // one step to save photos and another step
            // to submit them.
            verificationModel = new edx.verify_student.VerificationModel();

            _.each(this.stepOrder, function(name, index) {
                var stepView = new stepViewConstructors[name]({
                    errorModel: this.errorModel,
                    nextStepTitle: nextStepTitles[index],
                    stepData: stepInfo[name],
                    model: verificationModel
                });

                this.listenTo(stepView, 'next-step', this.nextStep);
                this.listenTo(stepView, 'go-to-step', this.goToStep);

                this.stepViews[name] = stepView;
            }, this);
        },

        render: function() {
            this.renderCurrentStep();
            return this;
        },

        renderCurrentStep: function() {
            var stepView, stepEl;

            // Get or create the step container
            stepEl = $("#current-step-container");
            if (!stepEl.length) {
                stepEl = $('<div id="current-step-container"></div>').appendTo(this.el);
            }

            // Render the step subview
            // When the view is rendered, it will overwrite the existing step in the DOM.
            stepView = this.stepViews[ this.stepOrder[ this.currentStepIndex ] ];
            stepView.el = stepEl;
            stepView.render();
        },

        nextStep: function() {
            this.currentStepIndex = Math.min(
                this.currentStepIndex + 1,
                this.stepOrder.length - 1
            );
            this.render();
        },

        goToStep: function( stepName ) {
            var stepIndex = _.indexOf(this.stepOrder, stepName);

            if ( stepIndex >= 0 ) {
                this.currentStepIndex = stepIndex;
            }

            this.render();
        }
    });

})(jQuery, _, Backbone, gettext);
