// eslint-disable-next-line no-undef
define([
    'jquery',
    'backbone',
    'common/js/spec_helpers/template_helpers',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'js/verify_student/views/image_input_view',
    'js/verify_student/models/verification_model'
], function($, Backbone, TemplateHelpers, AjaxHelpers, ImageInputView, VerificationModel) {
    'use strict';

    describe('edx.verify_student.ImageInputView', function() {
        // eslint-disable-next-line no-var
        var IMAGE_DATA = 'abcd1234';

        // eslint-disable-next-line no-var
        var createView = function() {
            return new ImageInputView({
                el: $('#current-step-container'),
                model: new VerificationModel({}),
                modelAttribute: 'faceImage',
                errorModel: new (Backbone.Model.extend({}))(),
                submitButton: $('#submit_button')
            }).render();
        };

        // eslint-disable-next-line no-var
        var uploadImage = function(view, fileType) {
            // eslint-disable-next-line no-var
            var deferred = $.Deferred();

            // Since image upload is an asynchronous process,
            // we need to wait for the upload to complete
            // before checking the outcome.
            // eslint-disable-next-line no-var
            var fakeFile,
                fakeEvent = {target: {files: []}};

            // If no file type is specified, don't add any files.
            // This simulates what happens when the user clicks
            // "cancel" after clicking the input.
            if (fileType !== null) {
                fakeFile = new Blob(
                    [IMAGE_DATA],
                    {type: 'image/' + fileType}
                );
                fakeEvent.target.files = [fakeFile];
            }

            // Wait for either a successful upload or an error
            view.on('imageCaptured', function() {
                deferred.resolve();
            });
            view.on('error', function() {
                deferred.resolve();
            });

            // Trigger the file input change
            // It's impossible to trigger this directly due
            // to browser security restrictions, so we call
            // the handler instead.
            view.handleInputChange(fakeEvent);

            return deferred.promise();
        };

        // eslint-disable-next-line no-var
        var expectPreview = function(view, fileType) {
            // eslint-disable-next-line no-var
            var previewImage = view.$preview.attr('src');
            if (fileType) {
                expect(previewImage).toContain('data:image/' + fileType);
            } else {
                expect(previewImage).toEqual('');
            }
        };

        // eslint-disable-next-line no-var
        var expectSubmitEnabled = function(isEnabled) {
            // eslint-disable-next-line no-var
            var appearsDisabled = $('#submit_button').hasClass('is-disabled'),
                isDisabled = $('#submit_button').prop('disabled');

            expect(!appearsDisabled).toEqual(isEnabled);
            expect(!isDisabled).toEqual(isEnabled);
        };

        // eslint-disable-next-line no-var
        var expectImageData = function(view, fileType) {
            // eslint-disable-next-line no-var
            var imageData = view.model.get(view.modelAttribute);
            if (fileType) {
                expect(imageData).toContain('data:image/' + fileType);
            } else {
                expect(imageData).toEqual('');
            }
        };

        // eslint-disable-next-line no-var
        var expectError = function(view) {
            expect(view.errorModel.get('shown')).toBe(true);
        };

        beforeEach(function() {
            setFixtures(
                '<div id="current-step-container"></div>'
                + '<input type="button" id="submit_button"></input>'
            );
            TemplateHelpers.installTemplate('templates/verify_student/image_input');
        });

        it('initially disables the submit button', function() {
            createView();
            expectSubmitEnabled(false);
        });

        it('uploads a png image', function(done) {
            // eslint-disable-next-line no-var
            var view = createView();

            uploadImage(view, 'png').then(function() {
                expectPreview(view, 'png');
                expectSubmitEnabled(true);
                expectImageData(view, 'png');
            }).always(done);
        });

        it('uploads a jpeg image', function(done) {
            // eslint-disable-next-line no-var
            var view = createView();

            uploadImage(view, 'jpeg').then(function() {
                expectPreview(view, 'jpeg');
                expectSubmitEnabled(true);
                expectImageData(view, 'jpeg');
            }).always(done);
        });

        it('hides the preview when the user cancels the upload', function(done) {
            // eslint-disable-next-line no-var
            var view = createView();

            uploadImage(view, null).then(function() {
                expectPreview(view, null);
                expectSubmitEnabled(false);
                expectImageData(view, null);
            }).always(done);
        });

        it('shows an error if the file type is not supported', function(done) {
            // eslint-disable-next-line no-var
            var view = createView();

            uploadImage(view, 'txt').then(function() {
                expectPreview(view, null);
                expectError(view);
                expectSubmitEnabled(false);
                expectImageData(view, null);
            }).always(done);
        });
    });
});
