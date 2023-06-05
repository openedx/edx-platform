/**
 * Allow users to upload an image using a file input.
 *
 * This uses HTML Media Capture so that iOS will
 * allow users to use their camera instead of choosing
 * a file.
 */

 var edx = edx || {};

 (function($, _, Backbone, gettext) {
     'use strict';

     edx.verify_student = edx.verify_student || {};

     edx.verify_student.ImageInputView = Backbone.View.extend({

         template: '#image_input-tpl',

         initialize: function(obj) {
             this.$submitButton = obj.submitButton ? $(obj.submitButton) : '';
             this.modelAttribute = obj.modelAttribute || '';
             this.errorModel = obj.errorModel || null;
         },

         render: function() {
             var renderedHtml = edx.HtmlUtils.template($(this.template).html())({});
             edx.HtmlUtils.setHtml(
                 $(this.el),
                 renderedHtml
             );
            // Set the submit button to disabled by default
             this.setSubmitButtonEnabled(false);

             this.$input = $('input.image-upload');
             this.$preview = $('img.preview');
             this.$input.on('change', _.bind(this.handleInputChange, this));

            // Initially hide the preview
             this.displayImage(false);

             return this;
         },

         handleInputChange: function(event) {
             var files = event.target.files,
                 reader = new FileReader();
             if (files[0] && files[0].type.match('image.[png|jpg|jpeg]')) {
                 reader.onload = _.bind(this.handleImageUpload, this);
                 reader.onerror = _.bind(this.handleUploadError, this);
                 reader.readAsDataURL(files[0]);
             } else if (files.length === 0) {
                 this.handleUploadError(false);
             } else {
                 this.handleUploadError(true);
             }
         },

         handleImageUpload: function(event) {
             var imageData = event.target.result;
             this.model.set(this.modelAttribute, imageData);
             this.displayImage(imageData);
             this.setSubmitButtonEnabled(true);

            // Hide any errors we may have displayed previously
             if (this.errorModel) {
                 this.errorModel.set({shown: false});
             }

             this.trigger('imageCaptured');
         },

         displayImage: function(imageData) {
             if (imageData) {
                 this.$preview
                    .attr('src', imageData)
                    .removeClass('is-hidden')
                    .attr('aria-hidden', 'false');
             } else {
                 this.$preview
                    .attr('src', '')
                    .addClass('is-hidden')
                    .attr('aria-hidden', 'true');
             }
         },

         handleUploadError: function(displayError) {
             this.displayImage(null);
             this.setSubmitButtonEnabled(false);
             if (this.errorModel) {
                 if (displayError) {
                     this.errorModel.set({
                         errorTitle: gettext('Image Upload Error'),
                         errorMsg: gettext('Please verify that you have uploaded a valid image (PNG and JPEG).'),
                         shown: true
                     });
                 } else {
                     this.errorModel.set({
                         shown: false
                     });
                 }
             }
             this.trigger('error');
         },

         setSubmitButtonEnabled: function(isEnabled) {
             this.$submitButton
                .toggleClass('is-disabled', !isEnabled)
                .prop('disabled', !isEnabled)
                .attr('aria-disabled', !isEnabled);
         }
     });
 }(jQuery, _, Backbone, gettext));
