/**
 * Show a message to the student that he/she has successfully
 * submitted photos for reverification.
 */

 var edx = edx || {};

 (function() {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.ReverifySuccessStepView = edx.verify_student.StepView.extend({
        templateName: 'reverify_success_step'
    });

 })();
