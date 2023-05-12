/**
 * View for the "id photo" step of the payment/verification flow.
 */
/* eslint-disable-next-line no-use-before-define, no-var */
var edx = edx || {};

(function($) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.IDPhotoStepView = edx.verify_student.StepView.extend({

        templateName: 'id_photo_step',

        defaultContext: function() {
            return {
                platformName: ''
            };
        },

        postRender: function() {
            // eslint-disable-next-line no-var
            var webcam = edx.verify_student.getSupportedWebcamView({
                el: $('#idcam'),
                model: this.model,
                modelAttribute: 'identificationImage',
                submitButton: '#next_step_button',
                errorModel: this.errorModel,
                captureSoundPath: this.stepData.captureSoundPath
            }).render();

            // Track a virtual pageview, for easy funnel reconstruction.
            window.analytics.page('verification', this.templateName);

            this.listenTo(webcam, 'imageCaptured', function() {
                // Track the user's successful image capture
                window.analytics.track('edx.bi.user.identification_image.captured', {
                    category: 'verification'
                });
            });

            // eslint-disable-next-line no-undef
            $('#next_step_button').on('click', _.bind(this.nextStep, this));
        }
    });
// eslint-disable-next-line no-undef
}(jQuery));
