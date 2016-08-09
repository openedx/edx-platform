define([
    'jquery',
    'backbone',
    'common/js/spec_helpers/template_helpers',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'js/verify_student/views/webcam_photo_view',
    'js/verify_student/models/verification_model'
],
    function($, Backbone, TemplateHelpers, AjaxHelpers, WebcamPhotoView, VerificationModel) {
        'use strict';

        describe('edx.verify_student.WebcamPhotoView', function() {
            var IMAGE_DATA = 'abcd1234',
                VIDEO_ERROR_TITLE = 'video capture error',
                VIDEO_ERROR_MSG = 'video error msg';

            /**
            * For the purposes of these tests, we stub out the backend
            * video capture implementation.
            * This allows us to easily test the application logic
            * without needing to handle the subtleties of video capture
            * (especially cross-browser).
            * However, this means that the test suite does NOT adequately
            * cover the HTML5 / Flash webcam integration.  We will need
            * cross-browser manual testing to verify that this works correctly.
            */
            var StubBackend = function(name, isSupported, snapshotSuccess) {
                if (_.isUndefined(isSupported)) {
                    isSupported = true;
                }

                if (_.isUndefined(snapshotSuccess)) {
                    snapshotSuccess = true;
                }

                return {
                    name: name,
                    initialize: function() {},
                    isSupported: function() { return isSupported; },
                    snapshot: function() { return snapshotSuccess; },
                    getImageData: function() { return IMAGE_DATA; },
                    reset: function() {}
                };
            };

            var createView = function(backendStub) {
                return new WebcamPhotoView({
                    el: $('#current-step-container'),
                    model: new VerificationModel({}),
                    modelAttribute: 'faceImage',
                    errorModel: new (Backbone.Model.extend({}))(),
                    submitButton: $('#submit_button'),
                    backend: backendStub
                }).render();
            };

            var takeSnapshot = function() {
                $('#webcam_capture_button').click();
            };

            var resetWebcam = function() {
                $('#webcam_reset_button').click();
            };

            var expectButtonShown = function(obj) {
                var resetButton = $('#webcam_reset_button'),
                    captureButton = $('#webcam_capture_button');

                expect(captureButton.hasClass('is-hidden')).toBe(!obj.snapshot);
                expect(resetButton.hasClass('is-hidden')).toBe(!obj.reset);
            };

            var expectSubmitEnabled = function(isEnabled) {
                var appearsDisabled = $('#submit_button').hasClass('is-disabled'),
                    isDisabled = $('#submit_button').prop('disabled');

                expect(!appearsDisabled).toEqual(isEnabled);
                expect(!isDisabled).toEqual(isEnabled);
            };

            beforeEach(function() {
                window.analytics = jasmine.createSpyObj('analytics', ['track', 'page', 'trackLink']);

                setFixtures(
                    '<div id="current-step-container"></div>' +
                    '<input type="button" id="submit_button"></input>'
                );
                TemplateHelpers.installTemplate('templates/verify_student/webcam_photo');
            });

            it('takes a snapshot', function() {
                var view = createView(new StubBackend('html5'));

                // Spy on the backend
                spyOn(view.backend, 'snapshot').and.callThrough();

                // Initially, only the snapshot button is shown
                expectButtonShown({
                    snapshot: true,
                    reset: false
                });

                expectSubmitEnabled(false);

                // Take the snapshot
                takeSnapshot();

                // Expect that the backend was used to take the snapshot
                expect(view.backend.snapshot).toHaveBeenCalled();

                // Expect that buttons were updated
                expectButtonShown({
                    snapshot: false,
                    reset: true
                });
                expectSubmitEnabled(true);

                // Expect that the image data was saved to the model
                expect(view.model.get('faceImage')).toEqual(IMAGE_DATA);
            });

            it('resets the camera', function() {
                var view = createView(new StubBackend('html5'));

                // Spy on the backend
                spyOn(view.backend, 'reset').and.callThrough();

                // Take the snapshot, then reset
                takeSnapshot();
                resetWebcam();

                // Expect that the backend was reset
                expect(view.backend.reset).toHaveBeenCalled();

                // Expect that we're back to the initial button shown state
                expectButtonShown({
                    snapshot: true,
                    reset: false
                });
                expectSubmitEnabled(false);

                // Expect that the image data is wiped from the model
                expect(view.model.get('faceImage')).toEqual('');
            });

            it('displays an error if the snapshot fails', function() {
                var view = createView(new StubBackend('html5', true, false));

                // Take a snapshot
                takeSnapshot();

                // Do NOT expect an error displayed
                expect(view.errorModel.get('shown')).not.toBe(true);

                // Expect that the capture button is still enabled
                // so the user can retry.
                expectButtonShown({
                    snapshot: true,
                    reset: false
                });

                // Expect that submit is NOT enabled, since the user didn't
                // successfully take a snapshot.
                expectSubmitEnabled(false);
            });

            it('displays an error triggered by the backend', function() {
                var view = createView(new StubBackend('html5'));

                // Simulate an error triggered by the backend
                // This could occur at any point, including
                // while the video capture is being set up.
                view.backend.trigger('error', VIDEO_ERROR_TITLE, VIDEO_ERROR_MSG);

                // Verify that the error is displayed
                expect(view.errorModel.get('errorTitle')).toEqual(VIDEO_ERROR_TITLE);
                expect(view.errorModel.get('errorMsg')).toEqual(VIDEO_ERROR_MSG);
                expect(view.errorModel.get('shown')).toBe(true);

                // Expect that buttons are hidden
                expectButtonShown({
                    snapshot: false,
                    reset: false
                });
                expectSubmitEnabled(false);
            });
        });
    }
);
