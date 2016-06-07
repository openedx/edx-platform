/**
 * Reverification flow.
 *
 * This flow allows students who have a denied or expired verification
 * to re-submit face and ID photos.  It re-uses most of the same sub-views
 * as the payment/verification flow.
 */
 var edx = edx || {};

 (function( $, _ ) {
    'use strict';
    var errorView,
        el = $('#reverify-container');

    edx.verify_student = edx.verify_student || {};

    // Initialize an error view for displaying top-level error messages.
    errorView = new edx.verify_student.ErrorView({
        el: $('#error-container')
    });

    // Initialize the base view, passing in information
    // from the data attributes on the parent div.
    return new edx.verify_student.ReverifyView({
        errorModel: errorView.model,
        stepInfo: {
            'face-photo-step': {
                platformName: el.data('platform-name'),
                captureSoundPath: el.data('capture-sound')
            },
            'id-photo-step': {
                platformName: el.data('platform-name'),
                captureSoundPath: el.data('capture-sound')
            },
            'review-photos-step': {
                fullName: el.data('full-name'),
                platformName: el.data('platform-name')
            },
            'reverify-success-step': {
                platformName: el.data('platform-name')
            }
        }
    }).render();
})( jQuery, _ );
