/**
 * View for the "face photo" step in the payment/verification flow.
 */
var edx = edx || {};

(function( $ ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.FacePhotoStepView = edx.verify_student.StepView.extend({

        postRender: function() {
            new edx.verify_student.WebcamPhotoView({
                el: $("#facecam"),
                model: this.model,
                modelAttribute: 'faceImage',
                submitButton: '#next_step_button'
            }).render();

            $('#next_step_button').click( _.bind( this.nextStep, this ) );
        },
    });

})( jQuery );
