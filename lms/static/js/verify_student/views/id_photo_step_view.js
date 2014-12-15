/**
 * View for the "id photo" step of the payment/verification flow.
 */
var edx = edx || {};

(function( $ ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.IDPhotoStepView = edx.verify_student.StepView.extend({

        postRender: function() {
            new edx.verify_student.WebcamPhotoView({
                el: $("#idcam"),
                model: this.model,
                modelAttribute: 'identificationImage',
                submitButton: '#next_step_button',
                errorModel: this.errorModel
            }).render();

            $('#next_step_button').on( 'click', _.bind( this.nextStep, this ) );
        },
    });

})( jQuery );
