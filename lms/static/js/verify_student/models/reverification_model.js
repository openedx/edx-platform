/**
 * Model for a reverification attempt.
 *
 * The re-verification model is responsible for
 * storing face photo image data and submitting
 * it back to the server.
 */
var edx = edx || {};

(function( $, _, Backbone ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.ReverificationModel = Backbone.Model.extend({

        defaults: {
            courseKey: '',
            checkpointName: '',
            faceImage: '',
        },

        sync: function( method ) {
            var model = this;
            var headers = { 'X-CSRFToken': $.cookie( 'csrftoken' ) },
                data = {
                    face_image: model.get( 'faceImage' ),
                },
                url = _.str.sprintf(
                    '/verify_student/reverify/%(courseKey)s/%(checkpointName)s/', {
                        courseKey: model.get('courseKey'),
                        checkpointName: model.get('checkpointName')
                    }
                );

            $.ajax({
                url: url,
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
