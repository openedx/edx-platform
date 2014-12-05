/**
 * View for the "review photos" step of the payment/verification flow.
 */
var edx = edx || {};

(function( $ ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.ReviewPhotosStepView = edx.verify_student.StepView.extend({

        postRender: function() {
            // TODO: submit the photos to Software Secure
            // TODO: disable the button until the user confirms
            $('#next_step_button').click( _.bind( this.nextStep, this ) );
        }
    });

})( jQuery );
