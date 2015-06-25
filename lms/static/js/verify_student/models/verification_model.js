/**
 * In-memory storage of verification photo data.
 *
 * This can be passed to multiple steps in the workflow
 * to persist image data in-memory before it is submitted
 * to the server.
 *
 */
 var edx = edx || {};

 (function( $, _, Backbone ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.VerificationModel = Backbone.Model.extend({

        defaults: {
            fullName: null,
            faceImage: "",
            identificationImage: ""
        },

        sync: function( method, model ) {
            var headers = { 'X-CSRFToken': $.cookie( 'csrftoken' ) },
                data = {
                    face_image: model.get( 'faceImage' ),
                    photo_id_image: model.get( 'identificationImage' )
                };

            // Full name is an optional parameter; if not provided,
            // it won't be changed.
            if ( !_.isEmpty( model.get( 'fullName' ) ) ) {
                data.full_name = model.get( 'fullName' );

                // Track the user's decision to change the name on their account
                window.analytics.track( 'edx.bi.user.full_name.changed', {
                    category: 'verification'
                });
            }

            // Submit the request to the server,
            // triggering events on success and error.
            $.ajax({
                url: '/verify_student/submit-photos/',
                type: 'POST',
                data: data,
                headers: headers,
                success: function() {
                    model.trigger( 'sync' );
                },
                error: function( error ) {
                    model.trigger( 'error', error );
                }
            });
        }
    });

 })( jQuery, _, Backbone );
