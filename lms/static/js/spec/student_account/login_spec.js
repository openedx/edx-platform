;(function (define) {
    'use strict';
    define([
            'jquery',
            'underscore',
            'common/js/spec_helpers/template_helpers',
            'common/js/spec_helpers/ajax_helpers',
            'js/student_account/models/LoginModel',
            'js/student_account/views/LoginView',
            'js/student_account/models/PasswordResetModel'
        ],
        function($, _, TemplateHelpers, AjaxHelpers, LoginModel, LoginView, PasswordResetModel) {

        describe('edx.student.account.LoginView', function() {
            var model = null,
                resetModel = null,
                view = null,
                requests = null,
                authComplete = false,
                PLATFORM_NAME = 'edX',
                USER_DATA = {
                    email: 'xsy@edx.org',
                    password: 'xsyisawesome',
                    remember: true
                },
                THIRD_PARTY_AUTH = {
                    currentProvider: null,
                    providers: [
                        {
                            id: 'oa2-google-oauth2',
                            name: 'Google',
                            iconClass: 'fa-google-plus',
                            loginUrl: '/auth/login/google-oauth2/?auth_entry=account_login',
                            registerUrl: '/auth/login/google-oauth2/?auth_entry=account_register'
                        },
                        {
                            id: 'oa2-facebook',
                            name: 'Facebook',
                            iconClass: 'fa-facebook',
                            loginUrl: '/auth/login/facebook/?auth_entry=account_login',
                            registerUrl: '/auth/login/facebook/?auth_entry=account_register'
                        }
                    ]
                },
                FORM_DESCRIPTION = {
                    method: 'post',
                    submit_url: '/user_api/v1/account/login_session/',
                    fields: [
                        {
                            placeholder: 'username@domain.com',
                            name: 'email',
                            label: 'Email',
                            defaultValue: '',
                            type: 'email',
                            required: true,
                            instructions: 'Enter your email.',
                            restrictions: {}
                        },
                        {
                            placeholder: '',
                            name: 'password',
                            label: 'Password',
                            defaultValue: '',
                            type: 'password',
                            required: true,
                            instructions: 'Enter your password.',
                            restrictions: {}
                        },
                        {
                            placeholder: '',
                            name: 'remember',
                            label: 'Remember me',
                            defaultValue: '',
                            type: 'checkbox',
                            required: true,
                            instructions: 'Agree to the terms of service.',
                            restrictions: {}
                        }
                    ]
                },
                COURSE_ID = 'edX/demoX/Fall';

            var createLoginView = function(test) {
                // Initialize the login model
                model = new LoginModel({}, {
                    url: FORM_DESCRIPTION.submit_url,
                    method: FORM_DESCRIPTION.method
                });

                // Initialize the passwordReset model
                resetModel = new PasswordResetModel({}, {
                    method: 'GET',
                    url: '#'
                });

                // Initialize the login view
                view = new LoginView({
                    fields: FORM_DESCRIPTION.fields,
                    model: model,
                    resetModel: resetModel,
                    thirdPartyAuth: THIRD_PARTY_AUTH,
                    platformName: PLATFORM_NAME
                });

                // Spy on AJAX requests
                requests = AjaxHelpers.requests(test);

                // Intercept events from the view
                authComplete = false;
                view.on("auth-complete", function() {
                    authComplete = true;
                });
            };

            var submitForm = function(validationSuccess) {
                // Create a fake click event
                var clickEvent = $.Event('click');

                // Simulate manual entry of login form data
                $('#login-email').val(USER_DATA.email);
                $('#login-password').val(USER_DATA.password);

                // Check the 'Remember me' checkbox
                $('#login-remember').prop('checked', USER_DATA.remember);

                // If validationSuccess isn't passed, we avoid
                // spying on `view.validate` twice
                if ( !_.isUndefined(validationSuccess) ) {
                    // Force validation to return as expected
                    spyOn(view, 'validate').andReturn({
                        isValid: validationSuccess,
                        message: 'Submission was validated.'
                    });
                }

                // Submit the email address
                view.submitForm(clickEvent);
            };

            beforeEach(function() {
                setFixtures('<div id="login-form"></div>');
                TemplateHelpers.installTemplate('templates/student_account/login');
                TemplateHelpers.installTemplate('templates/student_account/form_field');
            });

            it('logs the user in', function() {
                createLoginView(this);

                // Submit the form, with successful validation
                submitForm(true);

                // Form button should be disabled on success.
                expect(view.$submitButton).toHaveAttr('disabled');

                // Verify that the client contacts the server with the expected data
                AjaxHelpers.expectRequest(
                    requests, 'POST',
                    FORM_DESCRIPTION.submit_url,
                    $.param(USER_DATA)
                );

                // Respond with status code 200
                AjaxHelpers.respondWithJson(requests, {});

                // Verify that auth-complete is triggered
                expect(authComplete).toBe(true);
            });

            it('sends analytics info containing the enrolled course ID', function() {
                var expectedData;

                createLoginView(this);

                // Simulate that the user is attempting to enroll in a course
                // by setting the course_id query string param.
                spyOn($, 'url').andCallFake(function( param ) {
                    if (param === '?course_id') {
                        return encodeURIComponent( COURSE_ID );
                    }
                });

                // Attempt to login
                submitForm( true );

                // Verify that the client sent the course ID for analytics
                expectedData = {};
                $.extend(expectedData, USER_DATA, {
                    analytics: JSON.stringify({
                        enroll_course_id: COURSE_ID
                    })
                });

                AjaxHelpers.expectRequest(
                    requests, 'POST',
                    FORM_DESCRIPTION.submit_url,
                    $.param( expectedData )
                );
            });

            it('displays third-party auth login buttons', function() {
                createLoginView(this);

                // Verify that Google and Facebook registration buttons are displayed
                expect($('.button-oa2-google-oauth2')).toBeVisible();
                expect($('.button-oa2-facebook')).toBeVisible();
            });

            it('displays a link to the password reset form', function() {
                createLoginView(this);

                // Verify that the password reset link is displayed
                expect($('.forgot-password')).toBeVisible();
            });

            it('validates login form fields', function() {
                createLoginView(this);

                submitForm(true);

                // Verify that validation of form fields occurred
                expect(view.validate).toHaveBeenCalledWith($('#login-email')[0]);
                expect(view.validate).toHaveBeenCalledWith($('#login-password')[0]);
            });

            it('displays login form validation errors', function() {
                createLoginView(this);

                // Submit the form, with failed validation
                submitForm(false);

                // Verify that submission errors are visible
                expect(view.$errors).not.toHaveClass('hidden');

                // Expect auth complete NOT to have been triggered
                expect(authComplete).toBe(false);
                // Form button should be re-enabled when errors occur
                expect(view.$submitButton).not.toHaveAttr('disabled');
            });

            it('displays an error if the server returns an error while logging in', function() {
                createLoginView(this);

                // Submit the form, with successful validation
                submitForm(true);

                // Simulate an error from the LMS servers
                AjaxHelpers.respondWithError(requests);

                // Expect that an error is displayed and that auth complete is not triggered
                expect(view.$errors).not.toHaveClass('hidden');
                expect(authComplete).toBe(false);
                // Form button should be re-enabled on server failure.
                expect(view.$submitButton).not.toHaveAttr('disabled');

                // If we try again and succeed, the error should go away
                submitForm();

                // Form button should be disabled on success.
                expect(view.$submitButton).toHaveAttr('disabled');

                // This time, respond with status code 200
                AjaxHelpers.respondWithJson(requests, {});

                // Expect that the error is hidden and auth complete is triggered
                expect(view.$errors).toHaveClass('hidden');
                expect(authComplete).toBe(true);
            });

            it('displays an error if there is no internet connection', function () {
                createLoginView(this);

                // Submit the form, with successful validation
                submitForm(true);

                // Simulate an error from the LMS servers
                AjaxHelpers.respondWithError(requests, 0);

                // Expect that an error is displayed and that auth complete is not triggered
                expect(view.$errors).not.toHaveClass('hidden');
                expect(authComplete).toBe(false);
                expect(view.$errors.text()).toContain(
                    'An error has occurred. Check your Internet connection and try again.'
                );
            });
            it('displays an error if there is a server error', function () {
                createLoginView(this);

                // Submit the form, with successful validation
                submitForm(true);

                // Simulate an error from the LMS servers
                AjaxHelpers.respondWithError(requests, 500);

                // Expect that an error is displayed and that auth complete is not triggered
                expect(view.$errors).not.toHaveClass('hidden');
                expect(authComplete).toBe(false);
                expect(view.$errors.text()).toContain(
                    'An error has occurred. Try refreshing the page, or check your Internet connection.'
                );
            });
        });
    });
}).call(this, define || RequireJS.define);
