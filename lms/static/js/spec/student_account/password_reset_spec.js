define([
    'jquery',
    'underscore',
    'common/js/spec_helpers/template_helpers',
    'common/js/spec_helpers/ajax_helpers',
    'js/student_account/models/PasswordResetModel',
    'js/student_account/views/PasswordResetView',
], function($, _, TemplateHelpers, AjaxHelpers, PasswordResetModel, PasswordResetView) {
        describe('edx.student.account.PasswordResetView', function() {
            'use strict';

            var model = null,
                view = null,
                requests = null,
                EMAIL = 'xsy@edx.org',
                FORM_DESCRIPTION = {
                    method: 'post',
                    submit_url: '/account/password',
                    fields: [{
                        name: 'email',
                        label: 'Email',
                        defaultValue: '',
                        type: 'text',
                        required: true,
                        placeholder: 'place@holder.org',
                        instructions: 'Enter your email.',
                        restrictions: {}
                    }]
                };

            var createPasswordResetView = function(that) {
                // Initialize the password reset model
                model = new PasswordResetModel({}, {
                    url: FORM_DESCRIPTION.submit_url,
                    method: FORM_DESCRIPTION.method
                });

                // Initialize the password reset view
                view = new PasswordResetView({
                    fields: FORM_DESCRIPTION.fields,
                    model: model
                });

                // Spy on AJAX requests
                requests = AjaxHelpers.requests(that);
            };

            var submitEmail = function(validationSuccess) {
                // Simulate manual entry of an email address
                $('#password-reset-email').val(EMAIL);

                // Create a fake click event
                var clickEvent = $.Event('click');

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
                setFixtures('<div id="password-reset-form" class="form-wrapper hidden"></div>');
                TemplateHelpers.installTemplate('templates/student_account/password_reset');
                TemplateHelpers.installTemplate('templates/student_account/form_field');
            });

            it('allows the user to request a new password', function() {
                createPasswordResetView(this);

                // Submit the form, with successful validation
                submitEmail(true);

                // Verify that the client contacts the server with the expected data
                AjaxHelpers.expectRequest(
                    requests, 'POST',
                    FORM_DESCRIPTION.submit_url,
                    $.param({ email: EMAIL })
                );

                // Respond with status code 200
                AjaxHelpers.respondWithJson(requests, {});

                // Verify that the success message is visible
                expect($('.js-reset-success')).not.toHaveClass('hidden');

                // Verify that login form has loaded
                expect($('#login-form')).not.toHaveClass('hidden');

                // Verify that password reset view has been removed
                expect($( view.el ).html().length).toEqual(0);
            });

            it('validates the email field', function() {
                createPasswordResetView(this);

                // Submit the form, with successful validation
                submitEmail(true);

                // Verify that validation of the email field occurred
                expect(view.validate).toHaveBeenCalledWith($('#password-reset-email')[0]);

                // Verify that no submission errors are visible
                expect(view.$errors).toHaveClass('hidden');
            });

            it('displays password reset validation errors', function() {
                createPasswordResetView(this);

                // Submit the form, with failed validation
                submitEmail(false);

                // Verify that submission errors are visible
                expect(view.$errors).not.toHaveClass('hidden');
            });

            it('displays an error if the server returns an error while sending a password reset email', function() {
                createPasswordResetView(this);
                submitEmail(true);

                // Simulate an error from the LMS servers
                AjaxHelpers.respondWithError(requests);

                // Expect that an error is displayed
                expect(view.$errors).not.toHaveClass('hidden');

                // If we try again and succeed, the error should go away
                submitEmail();

                // This time, respond with status code 200
                AjaxHelpers.respondWithJson(requests, {});

                // Expect that the error is hidden
                expect(view.$errors).toHaveClass('hidden');
            });
        });
    }
);
