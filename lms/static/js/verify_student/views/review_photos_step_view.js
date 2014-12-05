/**
 * View for the "review photos" step of the payment/verification flow.
 */
var edx = edx || {};

(function( $, gettext ) {
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
            $( '.is-expandable .title-expand' ).on( 'click', this.expandCallback );

            // Disable the submit button until user confirmation
            $( '#confirm_pics_good' ).on( 'click', this.toggleSubmitEnabled );

            // Go back to the first photo step if we need to retake photos
            $( '#retake_photos_button' ).on( 'click', _.bind( this.retakePhotos, this ) );

            // When moving to the next step, submit photos for verification
            $( '#next_step_button' ).on( 'click', _.bind( this.submitPhotos, this ) );
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
            this.model.set( 'fullName', $( '#new-name' ).val() );
            this.model.save();
        },

        handleSubmissionError: function( xhr ) {
            // Re-enable the submit button to allow the user to retry
            var isConfirmChecked = $( "#confirm_pics_good" ).prop('checked');
            $( "#next_step_button" ).toggleClass( "is-disabled", !isConfirmChecked );

            // Display the error
            if ( xhr.status === 400 ) {
                this.errorModel.set({
                    errorTitle: gettext( 'Could not submit photos' ),
                    errorMsg: xhr.responseText,
                    shown: true
                });
            }
            else {
                this.errorModel.set({
                    errorTitle: gettext( 'Could not submit photos' ),
                    errorMsg: gettext( 'An unexpected error occurred.  Please try again later.' ),
                    shown: true
                });
            }
        },

        expandCallback: function(event) {
            event.preventDefault();

            $(this).next('.expandable-area' ).slideToggle();

            var title = $( this ).parent();
            title.toggleClass( 'is-expanded' );
            title.attr( 'aria-expanded', !title.attr('aria-expanded') );
        }
    });

})( jQuery, gettext );
