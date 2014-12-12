/**
 * In-memory storage of verification photo data.
 *
 * This can be passed to multiple steps in the workflow
 * to persist image data in-memory before it is submitted
 * to the server.
 *
 */
 var edx = edx || {};

 (function( $, Backbone ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.VerificationModel = Backbone.Model.extend({

        defaults: {
            fullName: null,
            facePhoto: "",
            identificationPhoto: ""
        },

        initialize: function( obj ) {
        },

        sync: function( method, model ) {

        }
    });

 })( jQuery, Backbone );
