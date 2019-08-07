/* globals _ */
/**
 * View for the "review photos" step of the payment/verification flow.
 */
var edx = edx || {};

(function($, gettext) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.ReviewPhotosStepView = edx.verify_student.StepView.extend({

        templateName: 'review_photos_step',

        defaultContext: function() {
            return {
                platformName: '',
                fullName: ''
            };
        },

        postRender: function() {
            // Load the photos from the previous steps
            $('#face_image')[0].src = this.model.get('faceImage');
            $('#photo_id_image')[0].src = this.model.get('identificationImage');

            // Prep the name change dropdown
            $('.expandable-area').slideUp();
            $('.is-expandable').addClass('is-ready');
            $('.is-expandable .title-expand').on('click', this.expandCallback);

            // Go back to the first photo step if we need to retake photos
            $('#retake_photos_button').on('click', _.bind(this.retakePhotos, this));

            // When moving to the next step, submit photos for verification
            $('#next_step_button').on('click', _.bind(this.submitPhotos, this));

            // Track a virtual pageview, for easy funnel reconstruction.
            window.analytics.page('verification', this.templateName);
        },

        retakePhotos: function() {
            // Track the user's intent to retake their photos
            window.analytics.track('edx.bi.user.images.retaken', {
                category: 'verification'
            });

            this.goToStep('face-photo-step');
        },

        submitPhotos: function() {
            var fullName = $('#new-name').val();

            // Disable the submit button to prevent duplicate submissions
            this.setSubmitButtonEnabled(false);

            // On success, move on to the next step
            this.listenToOnce(this.model, 'sync', _.bind(this.nextStep, this));

            // On failure, re-enable the submit button and display the error
            this.listenToOnce(this.model, 'error', _.bind(this.handleSubmissionError, this));

            // Submit
            if (fullName) {
                this.model.set('fullName', fullName);
            }
            this.model.save();
        },

        handleSubmissionError: function(xhr) {
            var errorMsg = gettext('An error has occurred. Please try again later.');

            // Re-enable the submit button to allow the user to retry
            this.setSubmitButtonEnabled(true);

            if (xhr.status === 400) {
                errorMsg = xhr.responseText;
            }

            this.errorModel.set({
                errorTitle: gettext('Could not submit photos'),
                errorMsg: errorMsg,
                shown: true
            });
        },

        expandCallback: function(event) {
            var $link = $(this),
                $title = $link.closest('.help-tip'),
                expanded = $title.hasClass('is-expanded');

            event.preventDefault();

            $link.attr('aria-expanded', !expanded);
            $title.toggleClass('is-expanded')
                  .find('.expandable-area').slideToggle();
        },

        setSubmitButtonEnabled: function(isEnabled) {
            $('#next_step_button')
                .toggleClass('is-disabled', !isEnabled)
                .prop('disabled', !isEnabled)
                .attr('aria-disabled', !isEnabled);
        }
    });
}(jQuery, gettext));
