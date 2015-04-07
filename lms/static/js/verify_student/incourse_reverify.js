/**
 * Set up the in-course reverification page.
 *
 * This loads data from the DOM's "data-*" attributes
 * and uses these to initialize the top-level views
 * on the page.
 */
 var edx = edx || {};

 (function( $, _ ) {
    'use strict';
    var errorView,
        el = $('#incourse-reverify-container');

    edx.verify_student = edx.verify_student || {};

    errorView = new edx.verify_student.ErrorView({
        el: $('#error-container')
    });

    return new edx.verify_student.InCourseReverifyView({
        courseKey: el.data('course-key'),
        checkpointName: el.data('checkpoint-name'),
        platformName: el.data('platform-name'),
        location: el.data('location'),
        errorModel: errorView.model
    }).render();

 })( jQuery, _ );
