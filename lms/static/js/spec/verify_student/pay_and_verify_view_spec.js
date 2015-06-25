define(['jquery', 'js/common_helpers/template_helpers', 'js/verify_student/views/pay_and_verify_view'],
    function( $, TemplateHelpers, PayAndVerifyView ) {
        'use strict';

        describe( 'edx.verify_student.PayAndVerifyView', function() {

            var TEMPLATES = [
                'enrollment_confirmation_step',
                'error',
                'face_photo_step',
                'id_photo_step',
                'intro_step',
                'make_payment_step',
                'payment_confirmation_step',
                'review_photos_step',
                'webcam_photo',
                'image_input'
            ];

            var INTRO_STEP = {
                templateName: "intro_step",
                name: "intro-step",
                title: "Intro"
            };

            var DISPLAY_STEPS_FOR_PAYMENT = [
                {
                    templateName: "make_payment_step",
                    name: "make-payment-step",
                    title: "Make Payment"
                },
                {
                    templateName: "payment_confirmation_step",
                    name: "payment-confirmation-step",
                    title: "Payment Confirmation"
                }
            ];

            var DISPLAY_STEPS_FOR_VERIFICATION = [
                {
                    templateName: "face_photo_step",
                    name: "face-photo-step",
                    title: "Take Face Photo"
                },
                {
                    templateName: "id_photo_step",
                    name: "id-photo-step",
                    title: "ID Photo"
                },
                {
                    templateName: "review_photos_step",
                    name: "review-photos-step",
                    title: "Review Photos"
                },
                {
                    templateName: "enrollment_confirmation_step",
                    name: "enrollment-confirmation-step",
                    title: "Enrollment Confirmation"
                }
            ];


            var createView = function( displaySteps, currentStep ) {
                return new PayAndVerifyView({
                    displaySteps: displaySteps,
                    currentStep: currentStep
                }).render();
            };

            var expectStepRendered = function( stepName, stepNum, numSteps ) {
                // Expect that the step container div rendered
                expect( $( '.' + stepName ).length > 0 ).toBe( true );
            };

            beforeEach(function() {
                window.analytics = jasmine.createSpyObj('analytics', ['track', 'page', 'trackLink']);

                setFixtures('<div id="pay-and-verify-container"></div>');
                $.each( TEMPLATES, function( index, templateName ) {
                    TemplateHelpers.installTemplate('templates/verify_student/' + templateName );
                });
            });

            it( 'renders payment and verification steps', function() {
                // Create the view, starting on the first step
                var view = createView(
                    DISPLAY_STEPS_FOR_PAYMENT.concat(DISPLAY_STEPS_FOR_VERIFICATION),
                    'make-payment-step'
                );

                // Verify that the first step rendered
                expectStepRendered('make-payment-step', 1, 6);

                // Iterate through the steps, ensuring that each is rendered
                view.nextStep();
                expectStepRendered('payment-confirmation-step', 2, 6);

                view.nextStep();
                expectStepRendered('face-photo-step', 3, 6);

                view.nextStep();
                expectStepRendered('id-photo-step', 4, 6);

                view.nextStep();
                expectStepRendered('review-photos-step', 5, 6);

                view.nextStep();
                expectStepRendered('enrollment-confirmation-step', 6, 6);

                // Going past the last step stays on the last step
                view.nextStep();
                expectStepRendered('enrollment-confirmation-step', 6, 6);
            });

            it( 'renders intro and verification steps', function() {
                var view = createView(
                    [INTRO_STEP].concat(DISPLAY_STEPS_FOR_VERIFICATION),
                    'intro-step'
                );

                // Verify that the first step rendered
                expectStepRendered('intro-step', 1, 5);

                // Iterate through the steps, ensuring that each is rendered
                view.nextStep();
                expectStepRendered('face-photo-step', 2, 5);

                view.nextStep();
                expectStepRendered('id-photo-step', 3, 5);

                view.nextStep();
                expectStepRendered('review-photos-step', 4, 5);

                view.nextStep();
                expectStepRendered('enrollment-confirmation-step', 5, 5);
            });

            it( 'starts from a later step', function() {
                // Start from the payment confirmation step
                var view = createView(
                    DISPLAY_STEPS_FOR_PAYMENT.concat(DISPLAY_STEPS_FOR_VERIFICATION),
                    'payment-confirmation-step'
                );

                // Verify that we start on the right step
                expectStepRendered('payment-confirmation-step', 2, 6);

                // Try moving to the next step
                view.nextStep();
                expectStepRendered('face-photo-step', 3, 6);

            });

            it( 'jumps to a particular step', function() {
                // Start on the review photos step
                var view = createView(
                    DISPLAY_STEPS_FOR_VERIFICATION,
                    'review-photos-step'
                );

                // Jump back to the face photo step
                view.goToStep('face-photo-step');
                expectStepRendered('face-photo-step', 1, 4);

            });
        });
    }
);
