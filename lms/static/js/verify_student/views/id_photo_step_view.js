/**
 * View for the "id photo" step of the payment/verification flow.
 */
var edx = edx || {};

(function( $ ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.IDPhotoStepView = edx.verify_student.StepView.extend({

        postRender: function() {
            $('#next_step_button').click( _.bind( this.nextStep, this ) );
        }
    });

})( jQuery );
