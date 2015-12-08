define(['backbone', 'jquery', 'underscore', 'common/js/spec_helpers/ajax_helpers', 'common/js/spec_helpers/template_helpers',
        'js/spec/student_account/helpers',
        'js/student_account/models/user_account_model',
        'js/student_profile/views/learner_profile_fields',
        'js/views/message_banner'
       ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, Helpers, UserAccountModel, LearnerProfileFields,
              MessageBannerView) {
        'use strict';

        describe("edx.user.LearnerProfileFields", function () {

            var MOCK_YEAR_OF_BIRTH = 1989;
            var MOCK_IMAGE_MAX_BYTES = 64;
            var MOCK_IMAGE_MIN_BYTES = 16;

            var createImageView = function (options) {
                var yearOfBirth = _.isUndefined(options.yearOfBirth) ? MOCK_YEAR_OF_BIRTH : options.yearOfBirth;
                var imageMaxBytes = _.isUndefined(options.imageMaxBytes) ? MOCK_IMAGE_MAX_BYTES : options.imageMaxBytes;
                var imageMinBytes = _.isUndefined(options.imageMinBytes) ? MOCK_IMAGE_MIN_BYTES : options.imageMinBytes;

                var imageData = {
                    image_url_large: '/media/profile-images/default.jpg',
                    has_image: options.hasImage ? true : false
                };

                var accountSettingsModel = new UserAccountModel();
                accountSettingsModel.set({'profile_image': imageData});
                accountSettingsModel.set({'year_of_birth': yearOfBirth});
                accountSettingsModel.set({'requires_parental_consent': _.isEmpty(yearOfBirth) ? true : false});

                accountSettingsModel.url = Helpers.USER_ACCOUNTS_API_URL;

                var messageView = new MessageBannerView({
                    el: $('.message-banner')
                });

                return new LearnerProfileFields.ProfileImageFieldView({
                    model: accountSettingsModel,
                    valueAttribute: "profile_image",
                    editable: options.ownProfile,
                    messageView: messageView,
                    imageMaxBytes: imageMaxBytes,
                    imageMinBytes: imageMinBytes,
                    imageUploadUrl: Helpers.IMAGE_UPLOAD_API_URL,
                    imageRemoveUrl: Helpers.IMAGE_REMOVE_API_URL
                });
            };

            beforeEach(function () {
                loadFixtures('js/fixtures/student_profile/student_profile.html');
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

            var initializeUploader = function (view) {
                view.$('.upload-button-input').fileupload({
                    url: Helpers.IMAGE_UPLOAD_API_URL,
                    type: 'POST',
                    add: view.fileSelected,
                    done: view.imageChangeSucceeded,
                    fail: view.imageChangeFailed
                });
            };

            describe("ProfileImageFieldView", function () {

                var verifyImageUploadButtonMessage = function (view, inProgress) {
                    var iconName = inProgress ? 'fa-spinner' : 'fa-camera';
                    var message = inProgress ? view.titleUploading : view.uploadButtonTitle();
                    expect(view.$('.upload-button-icon i').attr('class')).toContain(iconName);
                    expect(view.$('.upload-button-title').text().trim()).toBe(message);
                };

                var verifyImageRemoveButtonMessage = function (view, inProgress) {
                    var iconName = inProgress ? 'fa-spinner' : 'fa-remove';
                    var message = inProgress ? view.titleRemoving : view.removeButtonTitle();
                    expect(view.$('.remove-button-icon i').attr('class')).toContain(iconName);
                    expect(view.$('.remove-button-title').text().trim()).toBe(message);
                };

                it("can upload profile image", function() {

                    var imageView = createImageView({ownProfile: true, hasImage: false});
                    imageView.render();

                    var requests = AjaxHelpers.requests(this);
                    var imageName = 'profile_image.jpg';

                    initializeUploader(imageView);

                    // Remove button should not be present for default image
                    expect(imageView.$('.u-field-remove-button').css('display') === 'none').toBeTruthy();

                    // For default image, image title should be `Upload an image`
                    verifyImageUploadButtonMessage(imageView, false);

                    // Add image to upload queue. Validate the image size and send POST request to upload image
                    imageView.$('.upload-button-input').fileupload('add', {files: [createFakeImageFile(60)]});

                    // Verify image upload progress message
                    verifyImageUploadButtonMessage(imageView, true);

                    // Verify if POST request received for image upload
                    AjaxHelpers.expectRequest(requests, 'POST', Helpers.IMAGE_UPLOAD_API_URL, new FormData());

                    // Send 204 NO CONTENT to confirm the image upload success
                    AjaxHelpers.respondWithNoContent(requests);

                    // Upon successful image upload, account settings model will be fetched to
                    // get the url for newly uploaded image, So we need to send the response for that GET
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
                    verifyImageUploadButtonMessage(imageView, false);
                });

                it("can remove profile image", function() {

                    var imageView = createImageView({ownProfile: true, hasImage: false});
                    imageView.render();

                    var requests = AjaxHelpers.requests(this);

                    // Verify image remove title
                    verifyImageRemoveButtonMessage(imageView, false);

                    imageView.$('.u-field-remove-button').click();

                    // Verify image remove progress message
                    verifyImageRemoveButtonMessage(imageView, true);

                    // Verify if POST request received for image remove
                    AjaxHelpers.expectRequest(requests, 'POST', Helpers.IMAGE_REMOVE_API_URL, null);

                    // Send 204 NO CONTENT to confirm the image removal success
                    AjaxHelpers.respondWithNoContent(requests);

                    // Upon successful image removal, account settings model will be fetched to get default image url
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

                    var imageView = createImageView({ownProfile: true, hasImage: false});
                    imageView.render();

                    spyOn(imageView, 'clickedRemoveButton');

                    // Remove button should not be present for default image
                    expect(imageView.$('.u-field-remove-button').css('display') === 'none').toBeTruthy();

                    imageView.$('.u-field-remove-button').click();

                    // Remove button click handler should not be called
                    expect(imageView.clickedRemoveButton).not.toHaveBeenCalled();
                });

                it("can't upload image having size greater than max size", function() {

                    var imageView = createImageView({ownProfile: true, hasImage: false});
                    imageView.render();

                    initializeUploader(imageView);

                    // Add image to upload queue, this will validate the image size
                    imageView.$('.upload-button-input').fileupload('add', {files: [createFakeImageFile(70)]});

                    // Verify error message
                    expect($('.message-banner').text().trim())
                        .toBe('The file must be smaller than 64 bytes in size.');
                });

                it("can't upload image having size less than min size", function() {
                    var imageView = createImageView({ownProfile: true, hasImage: false});
                    imageView.render();

                    initializeUploader(imageView);

                    // Add image to upload queue, this will validate the image size
                    imageView.$('.upload-button-input').fileupload('add', {files: [createFakeImageFile(10)]});

                    // Verify error message
                    expect($('.message-banner').text().trim()).toBe('The file must be at least 16 bytes in size.');
                });

                it("can't upload and remove image if parental consent required", function() {

                    var imageView = createImageView({ownProfile: true, hasImage: false, yearOfBirth: ''});
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

                it("can't upload and remove image on others profile", function() {

                    var imageView = createImageView({ownProfile: false});
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
                    var imageView = createImageView({ownProfile: true, hasImage: false});
                    spyOn(imageView, 'onBeforeUnload');
                    imageView.render();

                    initializeUploader(imageView);

                    // Add image to upload queue, this will validate image size and send POST request to upload image
                    imageView.$('.upload-button-input').fileupload('add', {files: [createFakeImageFile(60)]});

                    // Verify image upload progress message
                    verifyImageUploadButtonMessage(imageView, true);

                    $(window).trigger('beforeunload');
                    expect(imageView.onBeforeUnload).toHaveBeenCalled();
                });

                it("shows error message for HTTP 500", function() {
                    var imageView = createImageView({ownProfile: true, hasImage: false});
                    imageView.render();

                    var requests = AjaxHelpers.requests(this);

                    initializeUploader(imageView);

                    // Add image to upload queue. Validate the image size and send POST request to upload image
                    imageView.$('.upload-button-input').fileupload('add', {files: [createFakeImageFile(60)]});

                    // Verify image upload progress message
                    verifyImageUploadButtonMessage(imageView, true);

                    // Verify if POST request received for image upload
                    AjaxHelpers.expectRequest(requests, 'POST', Helpers.IMAGE_UPLOAD_API_URL, new FormData());

                    // Send HTTP 500
                    AjaxHelpers.respondWithError(requests);

                    expect($('.message-banner').text().trim()).toBe(imageView.errorMessage);
                });
            });
        });
    });
