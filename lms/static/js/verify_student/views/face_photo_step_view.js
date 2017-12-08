/**
 * View for the "face photo" step in the payment/verification flow.
 */
var edx = edx || {};

(function($) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.FacePhotoStepView = edx.verify_student.StepView.extend({

        templateName: 'face_photo_step',

        defaultContext: function() {
            return {
                platformName: ''
            };
        },

        postRender: function() {
            var webcam = edx.verify_student.getSupportedWebcamView({
                el: $('#facecam'),
                model: this.model,
                modelAttribute: 'faceImage',
                submitButton: '#next_step_button',
                errorModel: this.errorModel,
                captureSoundPath: this.stepData.captureSoundPath
            }).render();

            // Track a virtual pageview, for easy funnel reconstruction.
            window.analytics.page('verification', this.templateName);

            this.listenTo(webcam, 'imageCaptured', function() {
                // Track the user's successful image capture
                window.analytics.track('edx.bi.user.face_image.captured', {
                    category: 'verification'
                });
            });

            $('#next_step_button').on('click', _.bind(this.nextStep, this));
        }
    });
}(jQuery));
