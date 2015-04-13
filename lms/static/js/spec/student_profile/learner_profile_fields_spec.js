define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/spec/student_account/helpers',
        'js/student_account/models/user_account_model',
        'js/student_profile/views/learner_profile_fields',
        'js/views/message_banner'
       ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, Helpers, UserAccountModel, LearnerProfileFields,
              MessageBannerView) {
        'use strict';

        describe("edx.user.LearnerProfileFields", function () {

            var createImageView = function (ownProfile, hasImage, imageMaxBytes, imageMinBytes, yearOfBirth) {

                var imageData = {
                    image_url_large: '/media/profile-images/default.jpg',
                    has_image: hasImage ? true : false
                };

                yearOfBirth = _.isUndefined(yearOfBirth) ? 1989 : yearOfBirth;

                var accountSettingsModel = new UserAccountModel();
                accountSettingsModel.set({'profile_image': imageData});
                accountSettingsModel.set({'year_of_birth': yearOfBirth});
                accountSettingsModel.set({'requires_parental_consent': _.isEmpty(yearOfBirth) ? true : false});

                accountSettingsModel.url = Helpers.USER_ACCOUNTS_API_URL;

                var messageView = new MessageBannerView({
                    el: $('.message-banner')
                });

                imageMaxBytes = imageMaxBytes || 64;
                imageMinBytes = imageMinBytes || 16;

                var editable = ownProfile ? 'toggle' : 'never';

                return new LearnerProfileFields.ProfileImageFieldView({
                    model: accountSettingsModel,
                    valueAttribute: "profile_image",
                    editable: editable === 'toggle',
                    messageView: messageView,
                    imageMaxBytes: imageMaxBytes,
                    imageMinBytes: imageMinBytes,
                    imageUploadUrl: Helpers.IMAGE_UPLOAD_API_URL,
                    imageRemoveUrl: Helpers.IMAGE_REMOVE_API_URL
                });
            };

            beforeEach(function () {
                setFixtures('<div class="message-banner"></div><div class="wrapper-profile"><div class="ui-loading-indicator"><p><span class="spin"><i class="icon fa fa-refresh"></i></span> <span class="copy">Loading</span></p></div><div class="ui-loading-error is-hidden"><i class="fa fa-exclamation-triangle message-error" aria-hidden=true></i><span class="copy">An error occurred. Please reload the page.</span></div></div>');
                TemplateHelpers.installTemplate('templates/student_profile/learner_profile');
                TemplateHelpers.installTemplate('templates/fields/field_image');
                TemplateHelpers.installTemplate("templates/fields/message_banner");
            });

            var createFakeImageFile = function (size) {
                var fileFakeData = 'i63ljc6giwoskyb9x5sw0169bdcmcxr3cdz8boqv0lik971972cmd6yknvcxr5sw0nvc169bdcmcxsdf';
                return new Blob(
                    [ fileFakeData.substr(0, size) ],
                    { type: 'image/jpg' }
                );
            };

            it("can upload profile image", function() {

                var imageView = createImageView(true, false);
                imageView.render();

                var requests = AjaxHelpers.requests(this);

                var imageName = 'profile_image.jpg';

                // Initialize jquery file uploader
                imageView.$('.upload-button-input').fileupload({
                    url: Helpers.IMAGE_UPLOAD_API_URL,
                    type: 'POST',
                    add: imageView.fileSelected,
                    done: imageView.imageChangeSucceeded,
                    fail: imageView.imageChangeFailed
                });

                // Remove button should not be present for default image
                expect(imageView.$('.u-field-remove-button').css('display') === 'none').toBeTruthy();

                // For default image, image title should be `Upload an image`
                expect(imageView.$('.upload-button-title').text().trim()).toBe(imageView.titleAdd);

                // Add image to upload queue, this will validate the image size and send POST request to upload image
                imageView.$('.upload-button-input').fileupload('add', {files: [createFakeImageFile(60)]});

                // Verify image upload progress message
                expect(imageView.$('.upload-button-title').text().trim()).toBe(imageView.titleUploading);

                // Verify if POST request received for image upload
                AjaxHelpers.expectRequest(requests, 'POST', Helpers.IMAGE_UPLOAD_API_URL, new FormData());

                // Send 204 NO CONTENT to confirm the image upload success
                AjaxHelpers.respondWithNoContent(requests);

                // Upon successful image upload, account settings model will be fetched to get the url for newly uploaded image
                // So we need to send the response for that GET
                var data = {profile_image: {
                    image_url_large: '/media/profile-images/' + imageName,
                    has_image: true
                }};
                AjaxHelpers.respondWithJson(requests, data);

                // Verify uploaded image name
                expect(imageView.$('.image-frame').attr('src')).toContain(imageName);

                // Remove button should be present after successful image upload
                expect(imageView.$('.u-field-remove-button').css('display') !== 'none').toBeTruthy();

                // After image upload, image title should be `Change image`
                expect(imageView.$('.upload-button-title').text().trim()).toBe(imageView.titleEdit);
            });

            it("can remove profile image", function() {
                var imageView = createImageView(true, true);
                imageView.render();

                var requests = AjaxHelpers.requests(this);

                imageView.$('.u-field-remove-button').click();

                // Verify image remove progress message
                expect(imageView.$('.remove-button-title').text().trim()).toBe(imageView.titleRemoving);

                // Verify if POST request received for image remove
                AjaxHelpers.expectRequest(requests, 'POST', Helpers.IMAGE_REMOVE_API_URL, null);

                // Send 204 NO CONTENT to confirm the image removal success
                AjaxHelpers.respondWithNoContent(requests);

                // Upon successful image removal, account settings model will be fetched to get the default image url
                // So we need to send the response for that GET
                var data = {profile_image: {
                    image_url_large: '/media/profile-images/default.jpg',
                    has_image: false
                }};
                AjaxHelpers.respondWithJson(requests, data);

                // Remove button should not be present for default image
                expect(imageView.$('.u-field-remove-button').css('display') === 'none').toBeTruthy();
            });

            it("can't remove default profile image", function() {
                var imageView = createImageView(true, false);
                imageView.render();

                spyOn(imageView, 'clickedRemoveButton');

                // Remove button should not be present for default image
                expect(imageView.$('.u-field-remove-button').css('display') === 'none').toBeTruthy();

                imageView.$('.u-field-remove-button').click();

                // Remove button click handler should not be called
                expect(imageView.clickedRemoveButton).not.toHaveBeenCalled();
            });

            it("can't upload image having size greater than max size", function() {
                var imageView = createImageView(true, false);
                imageView.render();

                // Initialize jquery file uploader
                imageView.$('.upload-button-input').fileupload({
                    url: Helpers.IMAGE_UPLOAD_API_URL,
                    type: 'POST',
                    add: imageView.fileSelected,
                    done: imageView.imageChangeSucceeded,
                    fail: imageView.imageChangeFailed
                });

                // Add image to upload queue, this will validate the image size
                imageView.$('.upload-button-input').fileupload('add', {files: [createFakeImageFile(70)]});

                // Verify error message
                expect($('.message-banner').text().trim()).toBe('Your image must be smaller than 64 Bytes in size.');
            });

            it("can't upload image having size less than min size", function() {
                var imageView = createImageView(true, false);
                imageView.render();

                // Initialize jquery file uploader
                imageView.$('.upload-button-input').fileupload({
                    url: Helpers.IMAGE_UPLOAD_API_URL,
                    type: 'POST',
                    add: imageView.fileSelected,
                    done: imageView.imageChangeSucceeded,
                    fail: imageView.imageChangeFailed
                });

                // Add image to upload queue, this will validate the image size
                imageView.$('.upload-button-input').fileupload('add', {files: [createFakeImageFile(10)]});

                // Verify error message
                expect($('.message-banner').text().trim()).toBe('Your image must be at least 16 Bytes in size.');
            });

            it("can't upload/remove image if parental consent required", function() {
                var imageView = createImageView(true, false, 64, 16, '');
                imageView.render();

                spyOn(imageView, 'clickedUploadButton');
                spyOn(imageView, 'clickedRemoveButton');

                expect(imageView.$('.u-field-upload-button').css('display') === 'none').toBeTruthy();
                expect(imageView.$('.u-field-remove-button').css('display') === 'none').toBeTruthy();

                imageView.$('.u-field-upload-button').click();
                imageView.$('.u-field-remove-button').click();

                expect(imageView.clickedUploadButton).not.toHaveBeenCalled();
                expect(imageView.clickedRemoveButton).not.toHaveBeenCalled();
            });

            it("can't upload image on others profile", function() {
                var imageView = createImageView(false);
                imageView.render();

                spyOn(imageView, 'clickedUploadButton');
                spyOn(imageView, 'clickedRemoveButton');

                expect(imageView.$('.u-field-upload-button').css('display') === 'none').toBeTruthy();
                expect(imageView.$('.u-field-remove-button').css('display') === 'none').toBeTruthy();

                imageView.$('.u-field-upload-button').click();
                imageView.$('.u-field-remove-button').click();

                expect(imageView.clickedUploadButton).not.toHaveBeenCalled();
                expect(imageView.clickedRemoveButton).not.toHaveBeenCalled();
            });

            it("shows message if we try to navigate away during image upload/remove", function() {
                var imageView = createImageView(true, false);
                spyOn(imageView, 'onBeforeUnload');
                imageView.render();

                // Initialize jquery file uploader
                imageView.$('.upload-button-input').fileupload({
                    url: Helpers.IMAGE_UPLOAD_API_URL,
                    type: 'POST',
                    add: imageView.fileSelected,
                    done: imageView.imageChangeSucceeded,
                    fail: imageView.imageChangeFailed
                });

                // Add image to upload queue, this will validate the image size and send POST request to upload image
                imageView.$('.upload-button-input').fileupload('add', {files: [createFakeImageFile(60)]});

                // Verify image upload progress message
                expect(imageView.$('.upload-button-title').text().trim()).toBe(imageView.titleUploading);

                $(window).trigger('beforeunload');

                expect(imageView.onBeforeUnload).toHaveBeenCalled();
            });

            it('renders message correctly', function() {
                var messageSelector = '.message-banner';
                var messageView = new MessageBannerView({
                    el: $(messageSelector)
                });

                messageView.showMessage('I am message view');
                // Verify error message
                expect($(messageSelector).text().trim()).toBe('I am message view');

                messageView.hideMessage();
                expect($(messageSelector).text().trim()).toBe('');
            });
        });
    });
