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
            faceImage: '',
            usageId: ''
        },

        sync: function( method ) {
            var model = this;
            var headers = { 'X-CSRFToken': $.cookie( 'csrftoken' ) },
                data = {
                    face_image: model.get( 'faceImage' )
                },
                url = _.str.sprintf(
                    '/verify_student/reverify/%(courseKey)s/%(usageId)s/', {
                        courseKey: model.get('courseKey'),
                        usageId: model.get('usageId')
                    }
                );

            $.ajax({
                url: url,
                type: 'POST',
                data: data,
                headers: headers,
                success: function(response) {
                    model.trigger( 'sync', response.url);
                },
                error: function( error ) {
                    model.trigger( 'error', error );
                }
            });
        }
    });

})( jQuery, _, Backbone );
