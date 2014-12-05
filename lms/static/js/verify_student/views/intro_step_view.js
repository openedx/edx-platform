/**
 * View for the "intro step" of the payment/verification flow.
 */
var edx = edx || {};

(function( $ ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    // Currently, this view doesn't need to install any custom event handlers,
    // since the button in the template reloads the page with a
    // ?skip-intro=1 GET parameter.  The reason for this is that we
    // want to allow users to click "back" to see the requirements,
    // and if they reload the page we want them to stay on the
    // second step.
    edx.verify_student.IntroStepView = edx.verify_student.StepView.extend({});

})( jQuery );
