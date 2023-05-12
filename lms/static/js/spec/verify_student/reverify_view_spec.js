/**
* Tests for the reverification view.
* */
// eslint-disable-next-line no-undef
define(['jquery', 'common/js/spec_helpers/template_helpers', 'js/verify_student/views/review_photos_step_view',
    'js/verify_student/views/reverify_view'],
function($, TemplateHelpers, ReviewPhotosStepView, ReverifyView) {
    'use strict';

    describe('edx.verify_student.ReverifyView', function() {
        // eslint-disable-next-line no-var
        var TEMPLATES = [
            'webcam_photo',
            'image_input',
            'error',
            'face_photo_step',
            'id_photo_step',
            'review_photos_step',
            'reverify_success_step'
        ];

        // eslint-disable-next-line no-var
        var STEP_INFO = {
            'face-photo-step': {
                platformName: 'edX'
            },
            'id-photo-step': {
                platformName: 'edX'
            },
            'review-photos-step': {
                fullName: 'John Doe',
                platformName: 'edX'
            },
            'reverify-success-step': {
                platformName: 'edX'
            }
        };

        // eslint-disable-next-line no-var
        var createView = function() {
            return new ReverifyView({stepInfo: STEP_INFO}).render();
        };

        // eslint-disable-next-line no-var
        var expectStepRendered = function(stepName) {
            // Expect that the step container div rendered
            expect($('.' + stepName).length > 0).toBe(true);
        };

        beforeEach(function() {
            // eslint-disable-next-line no-undef
            window.analytics = jasmine.createSpyObj('analytics', ['track', 'page', 'trackLink']);
            // eslint-disable-next-line no-undef
            navigator.getUserMedia = jasmine.createSpy();

            setFixtures('<div id="reverify-container"></div>');
            $.each(TEMPLATES, function(index, templateName) {
                TemplateHelpers.installTemplate('templates/verify_student/' + templateName);
            });
        });

        it('renders verification steps', function() {
            // eslint-disable-next-line no-var
            var view = createView();

            // Go through the flow, verifying that each step renders
            // We rely on other unit tests to check the behavior of these subviews.
            expectStepRendered('face-photo-step');

            view.nextStep();
            expectStepRendered('id-photo-step');

            view.nextStep();
            expectStepRendered('review-photos-step');

            view.nextStep();
            expectStepRendered('reverify-success-step');
        });
    });
}
);
