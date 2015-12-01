/**
 * View for in-course reverification.
 *
 * This view is responsible for rendering the page
 * template, including any subviews (for photo capture).
 */
 var edx = edx || {};

 (function( $, _, _s, Backbone, gettext ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.InCourseReverifyView = Backbone.View.extend({

        el: '#incourse-reverify-container',
        templateId: '#incourse_reverify-tpl',
        submitButtonId: '#submit',

        events: {
            'click #submit': 'submitPhoto'
        },

        initialize: function( obj ) {
            _.mixin( _s.exports() );

            this.errorModel = obj.errorModel || null;
            this.courseKey = obj.courseKey || null;
            this.platformName = obj.platformName || null;
            this.usageId = obj.usageId || null;


            this.model = new edx.verify_student.VerificationModel({
                courseKey: this.courseKey,
                checkpoint: this.usageId
            });

            this.listenTo( this.model, 'sync', _.bind( this.handleSubmitPhotoSuccess, this ));
            this.listenTo( this.model, 'error', _.bind( this.handleSubmissionError, this ));
        },

        render: function() {
            var renderedTemplate = _.template(
                $( this.templateId ).html(),
                {
                    courseKey: this.courseKey,
                    platformName: this.platformName
                }
            );
            $( this.el ).html( renderedTemplate );

            // Render the webcam view *after* the parent view
            // so that the container div for the webcam
            // exists in the DOM.
            this.renderWebcam();

            return this;
        },

        renderWebcam: function() {
            edx.verify_student.getSupportedWebcamView({
                el: $( '#webcam' ),
                model: this.model,
                modelAttribute: 'faceImage',
                submitButton: this.submitButtonId,
                errorModel: this.errorModel
            }).render();
        },

        submitPhoto: function() {
            // disable the submit button to prevent multiple submissions.
            this.setSubmitButtonEnabled(false);
            this.model.save();
        },

        handleSubmitPhotoSuccess: function(redirect_url) {
            // Redirect back to the courseware at the checkpoint location
            window.location.href = redirect_url;
        },

        handleSubmissionError: function(xhr) {
            var errorMsg = gettext( 'An error has occurred. Please try again later.' );

            // Re-enable the submit button to allow the user to retry
            this.setSubmitButtonEnabled( true );

            if ( xhr.status === 400 ) {
                errorMsg = xhr.responseText;
            }

            this.errorModel.set({
                errorTitle: gettext( 'Could not submit photos' ),
                errorMsg: errorMsg,
                shown: true
            });
        },
        setSubmitButtonEnabled: function( isEnabled ) {
            $(this.submitButtonId)
                .toggleClass( 'is-disabled', !isEnabled )
                .prop( 'disabled', !isEnabled )
                .attr('aria-disabled', !isEnabled);
        }
    });
})(jQuery, _, _.str, Backbone, gettext);
