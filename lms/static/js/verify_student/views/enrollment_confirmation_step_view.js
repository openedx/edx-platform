/**
 * View for the "enrollment confirmation" step of
 * the payment/verification flow.
 */
var edx = edx || {};

(function( $ ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    // Currently, this step does not need to install any event handlers,
    // since the displayed information is static.
    edx.verify_student.EnrollmentConfirmationStepView = edx.verify_student.StepView.extend({});

})( jQuery );
