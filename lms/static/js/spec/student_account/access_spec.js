define([
    'jquery',
    'js/common_helpers/template_helpers',
    'js/common_helpers/ajax_helpers',
    'js/student_account/views/AccessView',
    'js/student_account/views/FormView',
    'js/student_account/enrollment',
    'js/student_account/shoppingcart',
    'js/student_account/emailoptin'
], function($, TemplateHelpers, AjaxHelpers, AccessView, FormView, EnrollmentInterface, ShoppingCartInterface) {
        describe('edx.student.account.AccessView', function() {
            'use strict';

            var requests = null,
                view = null,
                FORM_DESCRIPTION = {
                    method: 'post',
                    submit_url: '/submit',
                    fields: [
                        {
                            name: 'email',
                            label: 'Email',
                            defaultValue: '',
                            type: 'text',
                            required: true,
                            placeholder: 'xsy@edx.org',
                            instructions: 'Enter your email here.',
                            restrictions: {},
                        },
                        {
                            name: 'username',
                            label: 'Username',
                            defaultValue: '',
                            type: 'text',
                            required: true,
                            placeholder: 'Xsy',
                            instructions: 'Enter your username here.',
                            restrictions: {
                                max_length: 200
                            }
                        }
                    ]
                },
                FORWARD_URL = '/courseware/next',
                COURSE_KEY = 'edx/DemoX/Fall';

            var ajaxSpyAndInitialize = function(that, mode) {
                // Spy on AJAX requests
                requests = AjaxHelpers.requests(that);

                // Initialize the access view
                view = new AccessView({
                    mode: mode,
                    thirdPartyAuth: {
                        currentProvider: null,
                        providers: []
                    },
                    platformName: 'edX',
                    loginFormDesc: FORM_DESCRIPTION,
                    registrationFormDesc: FORM_DESCRIPTION,
                    passwordResetFormDesc: FORM_DESCRIPTION
                });

                // Mock the redirect call
                spyOn( view, 'redirect' ).andCallFake( function() {} );

                // Mock the enrollment and shopping cart interfaces
                spyOn( EnrollmentInterface, 'enroll' ).andCallFake( function() {} );
                spyOn( ShoppingCartInterface, 'addCourseToCart' ).andCallFake( function() {} );
            };

            var assertForms = function(visibleType, hiddenType) {
                expect($(visibleType)).not.toHaveClass('hidden');
                expect($(hiddenType)).toHaveClass('hidden');
                expect($('#password-reset-form')).toHaveClass('hidden');
            };

            var selectForm = function(type) {
                // Create a fake change event to control form toggling
                var changeEvent = $.Event('change');
                changeEvent.currentTarget = $('.form-toggle[data-type="' + type + '"]');

                // Load form corresponding to the change event
                view.toggleForm(changeEvent);
            };

            /**
             * Simulate query string params.
             *
             * @param {object} params Parameters to set, each of which
             * should be prefixed with '?'
             */
            var setFakeQueryParams = function( params ) {
                spyOn( $, 'url' ).andCallFake(function( requestedParam ) {
                    if ( params.hasOwnProperty(requestedParam) ) {
                        return params[requestedParam];
                    }
                });
            };

            beforeEach(function() {
                setFixtures('<div id="login-and-registration-container"></div>');
                TemplateHelpers.installTemplate('templates/student_account/access');
                TemplateHelpers.installTemplate('templates/student_account/login');
                TemplateHelpers.installTemplate('templates/student_account/register');
                TemplateHelpers.installTemplate('templates/student_account/password_reset');
                TemplateHelpers.installTemplate('templates/student_account/form_field');

                // Stub analytics tracking
                window.analytics = jasmine.createSpyObj('analytics', ['track', 'page', 'pageview', 'trackLink']);
            });

            it('can initially display the login form', function() {
                ajaxSpyAndInitialize(this, 'login');

                /* Verify that the login form is expanded, and that the
                /* registration form is collapsed.
                 */
                assertForms('#login-form', '#register-form');
            });

            it('can initially display the registration form', function() {
                ajaxSpyAndInitialize(this, 'register');

                /* Verify that the registration form is expanded, and that the
                /* login form is collapsed.
                 */
                assertForms('#register-form', '#login-form');
            });

            it('toggles between the login and registration forms', function() {
                ajaxSpyAndInitialize(this, 'login');

                // Prevent URL from updating
                spyOn(history, 'pushState').andCallFake( function() {} );

                // Simulate selection of the registration form
                selectForm('register');
                assertForms('#register-form', '#login-form');

                // Simulate selection of the login form
                selectForm('login');
                assertForms('#login-form', '#register-form');
            });

            it('displays the reset password form', function() {
                ajaxSpyAndInitialize(this, 'login');

                // Simulate a click on the reset password link
                view.resetPassword();

                // Verify that the password reset wrapper is populated
                expect($('#password-reset-wrapper')).not.toBeEmpty();
            });

            it('enrolls the user on auth complete', function() {
                ajaxSpyAndInitialize(this, 'login');

                // Simulate providing enrollment query string params
                setFakeQueryParams({
                    '?enrollment_action': 'enroll',
                    '?course_id': COURSE_KEY
                });

                // Trigger auth complete on the login view
                view.subview.login.trigger('auth-complete');

                // Expect that the view tried to enroll the student
                expect( EnrollmentInterface.enroll ).toHaveBeenCalledWith(
                    COURSE_KEY,
                    '/course_modes/choose/' + COURSE_KEY + '/'
                );
            });

            it('sends the user to the payment flow when the course mode is not honor', function() {
                ajaxSpyAndInitialize(this, 'login');

                // Simulate providing enrollment query string params
                // AND specifying a course mode.
                setFakeQueryParams({
                    '?enrollment_action': 'enroll',
                    '?course_id': COURSE_KEY,
                    '?course_mode': 'verified'
                });

                // Trigger auth complete on the login view
                view.subview.login.trigger('auth-complete');

                // Expect that the view tried to auto-enroll the student
                // with a redirect into the payment flow.
                expect( EnrollmentInterface.enroll ).toHaveBeenCalledWith(
                    COURSE_KEY,
                    '/verify_student/start-flow/' + COURSE_KEY + '/'
                );
            });

            it('sends the user to the student dashboard when the course mode is honor', function() {
                ajaxSpyAndInitialize(this, 'login');

                // Simulate providing enrollment query string params
                // AND specifying a course mode.
                setFakeQueryParams({
                    '?enrollment_action': 'enroll',
                    '?course_id': COURSE_KEY,
                    '?course_mode': 'honor'
                });

                // Trigger auth complete on the login view
                view.subview.login.trigger('auth-complete');

                // Expect that the view tried auto-enrolled the student
                // and sent the student to the dashboard
                // (skipping the payment flow).
                expect( EnrollmentInterface.enroll ).toHaveBeenCalledWith(COURSE_KEY, '/dashboard');
            });

            it('adds a white-label course to the shopping cart on auth complete', function() {
                ajaxSpyAndInitialize(this, 'register');

                // Simulate providing "add to cart" query string params
                setFakeQueryParams({
                    '?enrollment_action': 'add_to_cart',
                    '?course_id': COURSE_KEY
                });

                // Trigger auth complete on the register view
                view.subview.register.trigger('auth-complete');

                // Expect that the view tried to add the course to the user's shopping cart
                expect( ShoppingCartInterface.addCourseToCart ).toHaveBeenCalledWith( COURSE_KEY );
            });

            it('redirects the user to the dashboard on auth complete', function() {
                ajaxSpyAndInitialize(this, 'register');

                // Trigger auth complete
                view.subview.register.trigger('auth-complete');

                // Since we did not provide a ?next query param, expect a redirect to the dashboard.
                expect( view.redirect ).toHaveBeenCalledWith( '/dashboard' );
            });

            it('redirects the user to the next page on auth complete', function() {
                ajaxSpyAndInitialize(this, 'register');

                // Simulate providing a ?next query string parameter
                setFakeQueryParams({ '?next': FORWARD_URL });

                // Trigger auth complete
                view.subview.register.trigger('auth-complete');

                // Verify that we were redirected
                expect( view.redirect ).toHaveBeenCalledWith( FORWARD_URL );
            });

            it('ignores redirect to external URLs', function() {
                ajaxSpyAndInitialize(this, 'register');

                // Simulate providing a ?next query string parameter
                // that goes to an external URL
                setFakeQueryParams({ '?next': "http://www.example.com" });

                // Trigger auth complete
                view.subview.register.trigger('auth-complete');

                // Expect that we ignore the external URL and redirect to the dashboard
                expect( view.redirect ).toHaveBeenCalledWith( "/dashboard" );
            });

        });
    }
);
