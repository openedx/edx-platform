;(function (define) {
    'use strict';
    define([
            'jquery',
            'underscore',
            'common/js/spec_helpers/template_helpers',
            'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
            'js/student_account/models/RegisterModel',
            'js/student_account/views/RegisterView'
        ],
        function($, _, TemplateHelpers, AjaxHelpers, RegisterModel, RegisterView) {

        describe('edx.student.account.RegisterView', function() {
            var model = null,
                view = null,
                requests = null,
                authComplete = false,
                PLATFORM_NAME = 'edX',
                COURSE_ID = 'edX/DemoX/Fall',
                USER_DATA = {
                    email: 'xsy@edx.org',
                    name: 'Xsy M. Education',
                    username: 'Xsy',
                    password: 'xsyisawesome',
                    level_of_education: 'p',
                    gender: 'm',
                    year_of_birth: 2014,
                    mailing_address: '141 Portland',
                    goals: 'To boldly learn what no letter of the alphabet has learned before',
                    honor_code: true
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
                    submit_url: '/user_api/v1/account/registration/',
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
                            placeholder: 'Jane Doe',
                            name: 'name',
                            label: 'Full Name',
                            defaultValue: '',
                            type: 'text',
                            required: true,
                            instructions: 'Enter your username.',
                            restrictions: {}
                        },
                        {
                            placeholder: 'JaneDoe',
                            name: 'username',
                            label: 'Username',
                            defaultValue: '',
                            type: 'text',
                            required: true,
                            instructions: 'Enter your username.',
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
                            name: 'level_of_education',
                            label: 'Highest Level of Education Completed',
                            defaultValue: '',
                            type: 'select',
                            options: [
                                {value: "", name: "--"},
                                {value: "p", name: "Doctorate"},
                                {value: "m", name: "Master's or professional degree"},
                                {value: "b", name: "Bachelor's degree"}
                            ],
                            required: false,
                            instructions: 'Select your education level.',
                            restrictions: {}
                        },
                        {
                            placeholder: '',
                            name: 'gender',
                            label: 'Gender',
                            defaultValue: '',
                            type: 'select',
                            options: [
                                {value: "", name: "--"},
                                {value: "m", name: "Male"},
                                {value: "f", name: "Female"},
                                {value: "o", name: "Other"}
                            ],
                            required: false,
                            instructions: 'Select your gender.',
                            restrictions: {}
                        },
                        {
                            placeholder: '',
                            name: 'year_of_birth',
                            label: 'Year of Birth',
                            defaultValue: '',
                            type: 'select',
                            options: [
                                {value: "", name: "--"},
                                {value: 1900, name: "1900"},
                                {value: 1950, name: "1950"},
                                {value: 2014, name: "2014"}
                            ],
                            required: false,
                            instructions: 'Select your year of birth.',
                            restrictions: {}
                        },
                        {
                            placeholder: '',
                            name: 'mailing_address',
                            label: 'Mailing Address',
                            defaultValue: '',
                            type: 'textarea',
                            required: false,
                            instructions: 'Enter your mailing address.',
                            restrictions: {}
                        },
                        {
                            placeholder: '',
                            name: 'goals',
                            label: 'Goals',
                            defaultValue: '',
                            type: 'textarea',
                            required: false,
                            instructions: "If you'd like, tell us why you're interested in edX.",
                            restrictions: {}
                        },
                        {
                            placeholder: '',
                            name: 'honor_code',
                            label: 'I agree to the <a href="/honor">Terms of Service and Honor Code</a>',
                            defaultValue: '',
                            type: 'checkbox',
                            required: true,
                            instructions: '',
                            restrictions: {}
                        }
                    ]
                };

            var createRegisterView = function(that) {
                // Initialize the register model
                model = new RegisterModel({}, {
                    url: FORM_DESCRIPTION.submit_url,
                    method: FORM_DESCRIPTION.method
                });

                // Initialize the register view
                view = new RegisterView({
                    fields: FORM_DESCRIPTION.fields,
                    model: model,
                    thirdPartyAuth: THIRD_PARTY_AUTH,
                    platformName: PLATFORM_NAME
                });

                // Spy on AJAX requests
                requests = AjaxHelpers.requests(that);

                // Intercept events from the view
                authComplete = false;
                view.on("auth-complete", function() {
                    authComplete = true;
                });
            };

            var submitForm = function(validationSuccess) {
                // Create a fake click event
                var clickEvent = $.Event('click');

                // Simulate manual entry of registration form data
                $('#register-email').val(USER_DATA.email);
                $('#register-name').val(USER_DATA.name);
                $('#register-username').val(USER_DATA.username);
                $('#register-password').val(USER_DATA.password);
                $('#register-level_of_education').val(USER_DATA.level_of_education);
                $('#register-gender').val(USER_DATA.gender);
                $('#register-year_of_birth').val(USER_DATA.year_of_birth);
                $('#register-mailing_address').val(USER_DATA.mailing_address);
                $('#register-goals').val(USER_DATA.goals);

                // Check the honor code checkbox
                $('#register-honor_code').prop('checked', USER_DATA.honor_code);

                // If validationSuccess isn't passed, we avoid
                // spying on `view.validate` twice
                if ( !_.isUndefined(validationSuccess) ) {
                    // Force validation to return as expected
                    spyOn(view, 'validate').and.returnValue({
                        isValid: validationSuccess,
                        message: 'Submission was validated.'
                    });
                }

                // Submit the email address
                view.submitForm(clickEvent);
            };

            beforeEach(function() {
                setFixtures('<div id="register-form"></div>');
                TemplateHelpers.installTemplate('templates/student_account/register');
                TemplateHelpers.installTemplate('templates/student_account/form_field');
            });

            it('registers a new user', function() {
                createRegisterView(this);

                // Submit the form, with successful validation
                submitForm(true);

                // Verify that the client contacts the server with the expected data
                AjaxHelpers.expectRequest(
                    requests, 'POST',
                    FORM_DESCRIPTION.submit_url,
                    $.param( USER_DATA )
                );

                // Respond with status code 200
                AjaxHelpers.respondWithJson(requests, {});

                // Verify that auth complete is triggered
                expect(authComplete).toBe(true);
                // Form button should be disabled on success.
                expect(view.$submitButton).toHaveAttr('disabled');
            });

            it('sends analytics info containing the enrolled course ID', function() {
                var expectedData;

                createRegisterView(this);

                // Simulate that the user is attempting to enroll in a course
                // by setting the course_id query string param.
                spyOn($, 'url').and.callFake(function( param ) {
                    if (param === '?course_id') {
                        return encodeURIComponent( COURSE_ID );
                    }
                });

                // Attempt to register
                submitForm( true );

                // Verify that the client sent the course ID for analytics
                expectedData = {course_id: COURSE_ID};
                $.extend(expectedData, USER_DATA);

                AjaxHelpers.expectRequest(
                    requests, 'POST',
                    FORM_DESCRIPTION.submit_url,
                    $.param( expectedData )
                );
            });

            it('displays third-party auth registration buttons', function() {
                createRegisterView(this);

                // Verify that Google and Facebook registration buttons are displayed
                expect($('.button-oa2-google-oauth2')).toBeVisible();
                expect($('.button-oa2-facebook')).toBeVisible();
            });

            it('validates registration form fields', function() {
                createRegisterView(this);

                // Submit the form, with successful validation
                submitForm(true);

                // Verify that validation of form fields occurred
                expect(view.validate).toHaveBeenCalledWith($('#register-email')[0]);
                expect(view.validate).toHaveBeenCalledWith($('#register-name')[0]);
                expect(view.validate).toHaveBeenCalledWith($('#register-username')[0]);
                expect(view.validate).toHaveBeenCalledWith($('#register-password')[0]);

                // Verify that no submission errors are visible
                expect(view.$errors).toHaveClass('hidden');
                // Form button should be disabled on success.
                expect(view.$submitButton).toHaveAttr('disabled');
            });

            it('displays registration form validation errors', function() {
                createRegisterView(this);

                // Submit the form, with failed validation
                submitForm(false);

                // Verify that submission errors are visible
                expect(view.$errors).not.toHaveClass('hidden');

                // Expect that auth complete is NOT triggered
                expect(authComplete).toBe(false);
                // Form button should be re-enabled on error.
                expect(view.$submitButton).not.toHaveAttr('disabled');
            });

            it('displays an error if the server returns an error while registering', function() {
                createRegisterView(this);

                // Submit the form, with successful validation
                submitForm(true);

                // Simulate an error from the LMS servers
                AjaxHelpers.respondWithError(requests);

                // Expect that an error is displayed and that auth complete is NOT triggered
                expect(view.$errors).not.toHaveClass('hidden');
                expect(authComplete).toBe(false);

                // If we try again and succeed, the error should go away
                submitForm();

                // This time, respond with status code 200
                AjaxHelpers.respondWithJson(requests, {});

                // Expect that the error is hidden and that auth complete is triggered
                expect(view.$errors).toHaveClass('hidden');
                expect(authComplete).toBe(true);
                // Form button should be disabled on success.
                expect(view.$submitButton).toHaveAttr('disabled');
            });
        });
    });
}).call(this, define || RequireJS.define);
