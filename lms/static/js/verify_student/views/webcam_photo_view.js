/**
 * Interface for retrieving webcam photos.
 * Supports both HTML5 and Flash.
 */
 var edx = edx || {};

 (function( $, _, Backbone ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.WebcamPhotoView = Backbone.View.extend({

        template: "#webcam_photo-tpl",

        initialize: function( obj ) {
            this.submitButton = obj.submitButton || "";
        },

        render: function() {
            var renderedHtml;

            // Load the template for the webcam into the DOM
            renderedHtml = _.template( $( this.template ).html(), {} );
            $( this.el ).html( renderedHtml );

            // Install event handlers
            $( "#webcam_reset_button", this.el ).click( _.bind( this.reset, this ) );
            $( "#webcam_capture_button", this.el ).click( _.bind( this.capture, this ) );
            $( "#webcam_approve_button", this.el ).click( _.bind( this.approve, this ) );

            return this;
        },

        reset: function() {
            // DEBUG
            console.log("Reset");

            // Disable the submit button
            $( this.submitButton ).addClass( "is-disabled" );

            // Go back to the initial button state
            $( "#webcam_reset_button", this.el ).hide();
            $( "#webcam_approve_button", this.el ).removeClass( "approved" ).hide();
            $( "#webcam_capture_button" ).show();
        },

        capture: function() {
            // DEBUG
            console.log("Capture");

            // Show the reset and approve buttons
            $( "#webcam_capture_button" ).hide();
            $( "#webcam_reset_button", this.el ).show();
            $( "#webcam_approve_button", this.el ).show();
        },

        approve: function() {
            // DEBUG
            console.log("Approve");

            // Make the "approve" button green
            $( "#webcam_approve_button" ).addClass( "approved" );

            // Enable the submit button
            $( this.submitButton ).removeClass( "is-disabled" );
        }
    });

 })( jQuery, _, Backbone );
