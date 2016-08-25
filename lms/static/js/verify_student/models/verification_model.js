/**
 * In-memory storage of verification photo data.
 *
 * This can be passed to multiple steps in the workflow
 * to persist image data in-memory before it is submitted
 * to the server.
 *
 */
 var edx = edx || {};

 (function($, Backbone) {
     'use strict';

     edx.verify_student = edx.verify_student || {};

     edx.verify_student.VerificationModel = Backbone.Model.extend({

         defaults: {
            // If provided, change the user's full name when submitting photos.
             fullName: null,

            // Image data for the user's face photo.
             faceImage: '',

            // Image data for the user's ID photo.
            // In the case of an in-course reverification, we won't
            // need to send this because we'll send the ID photo that
            // the user submitted with the initial verification attempt.
             identificationImage: null,

            // If the verification attempt is associated with a checkpoint
            // in a course, we send the the course and checkpoint location.
             courseKey: null,
             checkpoint: null
         },

         sync: function(method, model) {
             var headers = {'X-CSRFToken': $.cookie('csrftoken')},
                 data = {};

             data.face_image = model.get('faceImage');

            // The ID photo is optional, since in-course reverification
            // re-uses the image from the initial verification attempt.
             if (model.has('identificationImage')) {
                 data.photo_id_image = model.get('identificationImage');
             }

            // Full name is an optional parameter; if not provided,
            // it won't be changed.
             if (model.has('fullName')) {
                 data.full_name = model.get('fullName');

                // Track the user's decision to change the name on their account
                 window.analytics.track('edx.bi.user.full_name.changed', {
                     category: 'verification'
                 });
             }

            // If the user entered the verification flow from a checkpoint
            // in a course, we need to send the course and checkpoint
            // location to associate the attempt with the checkpoint.
             if (model.has('courseKey') && model.has('checkpoint')) {
                 data.course_key = model.get('courseKey');
                 data.checkpoint = model.get('checkpoint');
             }

            // Submit the request to the server,
            // triggering events on success and error.
             $.ajax({
                 url: '/verify_student/submit-photos/',
                 type: 'POST',
                 data: data,
                 headers: headers,
                 success: function(response) {
                     model.trigger('sync', response.url);
                 },
                 error: function(error) {
                     model.trigger('error', error);
                 }
             });
         }
     });
 })(jQuery, Backbone);
