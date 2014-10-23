define([
    'jquery',
    'js/common_helpers/template_helpers',
    'js/common_helpers/ajax_helpers',
    'js/student_account/views/AccessView',
    'js/student_account/views/FormView'
], function($, TemplateHelpers, AjaxHelpers, AccessView) {
        describe('edx.student.account.AccessView', function() {
            'use strict';

            var requests = null,
                view = null,
                AJAX_INFO = {
                    register: {
                        url: '/user_api/v1/account/registration/',
                        requestIndex: 1
                    },
                    login: {
                        url: '/user_api/v1/account/login_session/',
                        requestIndex: 0
                    },
                    password_reset: {
                        url: '/user_api/v1/account/password_reset/',
                        requestIndex: 1
                    }
                },
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
                };

            var ajaxAssertAndRespond = function(url, requestIndex) {
                // Verify that the client contacts the server as expected
                AjaxHelpers.expectJsonRequest(requests, 'GET', url, null, requestIndex);

                /* Simulate a response from the server containing
                /* a dummy form description
                 */
                AjaxHelpers.respondWithJson(requests, FORM_DESCRIPTION);
            };

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
                    platformName: 'edX'
                });

                ajaxAssertAndRespond(AJAX_INFO[mode].url);
            };

            var assertForms = function(visibleType, hiddenType) {
                expect($(visibleType)).not.toHaveClass('hidden');
                expect($(hiddenType)).toHaveClass('hidden');
                expect($('#password-reset-wrapper')).toBeEmpty();
            };

            var selectForm = function(type) {
                // Create a fake change event to control form toggling
                var changeEvent = $.Event('change');
                changeEvent.currentTarget = $('#' + type + '-option');

                // Load form corresponding to the change event
                view.toggleForm(changeEvent);

                ajaxAssertAndRespond(AJAX_INFO[type].url, AJAX_INFO[type].requestIndex);
            };

            beforeEach(function() {
                setFixtures('<div id="login-and-registration-container"></div>');
                TemplateHelpers.installTemplate('templates/student_account/access');
                TemplateHelpers.installTemplate('templates/student_account/login');
                TemplateHelpers.installTemplate('templates/student_account/register');
                TemplateHelpers.installTemplate('templates/student_account/password_reset');
                TemplateHelpers.installTemplate('templates/student_account/form_field');
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

                ajaxAssertAndRespond(
                    AJAX_INFO['password_reset'].url,
                    AJAX_INFO['password_reset'].requestIndex
                );

                // Verify that the password reset wrapper is populated
                expect($('#password-reset-wrapper')).not.toBeEmpty();
            });

            it('displays an error if a form definition could not be loaded', function() {
                // Spy on AJAX requests
                requests = AjaxHelpers.requests(this);

                // Init AccessView
                view = new AccessView({
                    mode: 'login',
                    thirdPartyAuth: {
                        currentProvider: null,
                        providers: []
                    },
                    platformName: 'edX'
                });

                // Simulate an error from the LMS servers
                AjaxHelpers.respondWithError(requests);

                // Error message should be displayed
                expect( $('#form-load-fail').hasClass('hidden') ).toBe(false);
            });
        });
    }
);
