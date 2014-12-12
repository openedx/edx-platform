/**
 * View for the "review photos" step of the payment/verification flow.
 */
var edx = edx || {};

(function( $ ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.ReviewPhotosStepView = edx.verify_student.StepView.extend({

        postRender: function() {
            // Disable the submit button until user confirmation
            $( "#confirm_pics_good" ).click( this.toggleSubmitEnabled );

            // Go back to the first photo step if we need to retake photos
            $( "#retake_photos_button" ).click( _.bind( this.retakePhotos, this ) );


            // TODO: submit the photos to Software Secure
            // TODO: disable the button until the user confirms
            $('#next_step_button').click( _.bind( this.nextStep, this ) );
        },

        toggleSubmitEnabled: function() {
            $( "#next_step_button" ).toggleClass( "is-disabled" );
        },

        retakePhotos: function() {
            this.goToStep( 'face-photo-step' );
        }
    });

})( jQuery );
