/**
 * Interface for retrieving webcam photos.
 * Supports both HTML5 and Flash.
 */
 var edx = edx || {};

 (function( $, _, Backbone ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.WebcamPhotoView = Backbone.View.extend({

        initialize: function( obj ) {
        },

        render: function() {
            return this;
        },
    });

 })( jQuery, _, Backbone );
