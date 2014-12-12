/**
 * View for the "review photos" step of the payment/verification flow.
 */
var edx = edx || {};

(function( $ ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.ReviewPhotosStepView = edx.verify_student.StepView.extend({

        postRender: function() {
            var model = this.model;

            // Load the photos from the previous steps
            $( "#face_image")[0].src = this.model.get('faceImage');
            $( "#photo_id_image")[0].src = this.model.get('identificationImage');

            // Prep the name change dropdown
            $( '.expandable-area' ).slideUp();
            $( '.is-expandable' ).addClass('is-ready');
            $( '.is-expandable .title-expand' ).click( this.expandCallback );

            // Disable the submit button until user confirmation
            $( '#confirm_pics_good' ).click( this.toggleSubmitEnabled );

            // Go back to the first photo step if we need to retake photos
            $( '#retake_photos_button' ).click( _.bind( this.retakePhotos, this ) );

            // When moving to the next step, submit photos for verification
            $( "#next_step_button" ).click( _.bind( this.submitPhotos, this ) );

            // TODO: Use edx.utils.validate
            $( '#new-name-button' ).click( function() {
                model.set({
                    fullName: $( '#new-name' ).val()
                });
            });
        },

        toggleSubmitEnabled: function() {
            $( '#next_step_button' ).toggleClass( 'is-disabled' );
        },

        retakePhotos: function() {
            this.goToStep( 'face-photo-step' );
        },

        submitPhotos: function() {
            // Disable the submit button to prevent duplicate submissions
            $( "#next_step_button" ).addClass( "is-disabled" );

            // On success, move on to the next step
            this.listenToOnce( this.model, 'sync', _.bind( this.nextStep, this ) );

            // On failure, re-enable the submit button and display the error
            this.listenToOnce( this.model, 'error', _.bind( this.handleSubmissionError, this ) );

            // Submit
            this.model.save();
        },

        handleSubmissionError: function() {
            // Re-enable the submit button to allow the user to retry
            var isConfirmChecked = $( "#confirm_pics_good" ).prop('checked');
            $( "#next_step_button" ).toggleClass( "is-disabled", !isConfirmChecked );

            // Display the error
            // TODO
            console.log("Photo submission error!");
        },

        // This should be done with pure CSS
        expandCallback: function(event) {
            event.preventDefault();

            $(this).next('.expandable-area' ).slideToggle();

            var title = $( this ).parent();
            title.toggleClass( 'is-expanded' );

            if ( title.attr( 'aria-expanded' ) === 'false' ) {
                title.attr( 'aria-expanded', 'true' );
            } else {
                title.attr( 'aria-expanded', 'false' );
            }
        }
    });

})( jQuery );
