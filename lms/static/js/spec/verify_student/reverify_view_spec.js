/**
* Tests for the reverification view.
**/
define(['jquery', 'common/js/spec_helpers/template_helpers', 'js/verify_student/views/review_photos_step_view',
        'js/verify_student/views/reverify_view'],
    function( $, TemplateHelpers, ReviewPhotosStepView, ReverifyView ) {
        'use strict';

        describe( 'edx.verify_student.ReverifyView', function() {

            var TEMPLATES = [
                "webcam_photo",
                "image_input",
                "error",
                "face_photo_step",
                "id_photo_step",
                "review_photos_step",
                "reverify_success_step"
            ];

            var STEP_INFO = {
                'face-photo-step': {
                    platformName: 'edX',
                },
                'id-photo-step': {
                    platformName: 'edX',
                },
                'review-photos-step': {
                    fullName: 'John Doe',
                    platformName: 'edX'
                },
                'reverify-success-step': {
                    platformName: 'edX'
                }
            };

            var createView = function() {
                return new ReverifyView({stepInfo: STEP_INFO}).render();
            };

            var expectStepRendered = function( stepName ) {
                // Expect that the step container div rendered
                expect( $( '.' + stepName ).length > 0 ).toBe( true );
            };


            beforeEach(function() {
                window.analytics = jasmine.createSpyObj('analytics', ['track', 'page', 'trackLink']);
                navigator.getUserMedia = jasmine.createSpy();

                setFixtures('<div id="reverify-container"></div>');
                $.each( TEMPLATES, function( index, templateName ) {
                    TemplateHelpers.installTemplate('templates/verify_student/' + templateName );
                });
            });

            it( 'renders verification steps', function() {
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
