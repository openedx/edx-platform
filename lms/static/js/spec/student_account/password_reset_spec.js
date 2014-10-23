define(['js/common_helpers/template_helpers', 'js/common_helpers/ajax_helpers', 'js/student_account/views/PasswordResetView'],
    function(TemplateHelpers, AjaxHelpers) {
        describe('edx.student.account.PasswordResetView', function() {
            'use strict';

            var view = null,
                ajaxSuccess = true,
                model = new edx.student.account.PasswordResetModel(),
                data = [{
                    label: 'E-mail',
                    instructions: 'This is the e-mail address you used to register with edX',
                    name: 'email',
                    required: true,
                    type: 'email',
                    restrictions: [],
                    defaultValue: ''
                }];

            var submitEmail = function(validationSuccess) {
                // Simulate manual entry of an email address
                $('#password-reset-email').val('foo@bar.baz');

                // Create a fake click event
                var clickEvent = $.Event('click');

                // If validationSuccess isn't passed, we avoid
                // spying on `view.validate` twice
                if (typeof validationSuccess !== 'undefined') {
                    // Force validation to return as expected
                    spyOn(view, 'validate').andReturn({
                        isValid: validationSuccess,
                        message: "We're all good."
                    });
                }

                // Submit the email address
                view.submitForm(clickEvent);
            };

            beforeEach(function() {
                setFixtures("<div id='password-reset-wrapper'></div>");
                TemplateHelpers.installTemplate('templates/student_account/password_reset');
                TemplateHelpers.installTemplate('templates/student_account/form_field');

                // Spy on AJAX requests
                requests = AjaxHelpers.requests(this);

                view = new edx.student.account.PasswordResetView({
                    fields: data,
                    model: model
                });
            });

            it("allows the user to request a new password", function() {
                submitEmail(true);

                // Verify that the client contacts the server
                AjaxHelpers.expectRequest(
                    requests, 'POST', '/account/password', $.param({email: EMAIL})
                );

                // Respond with status code 200
                AjaxHelpers.respondWithJson(requests, {});

                expect($('.js-reset-success')).not.toHaveClass('hidden');
            });

            it("validates the email field", function() {
                submitEmail(true);
                expect(view.validate).toHaveBeenCalled()
                expect(view.$errors).toHaveClass('hidden');
            });

            it("displays password reset validation errors", function() {
                submitEmail(false);
                expect(view.$errors).not.toHaveClass('hidden');
            });

            it("displays an error if the server cannot be contacted", function() {
                submitEmail(true);

                // Simulate an error from the LMS servers
                AjaxHelpers.respondWithError(requests);

                // Expect that an error is displayed
                expect(view.$'#submission-error').not.toHaveClass('hidden');

                // If we try again and succeed, the error should go away
                submitEmail();
                
                // This time, respond with status code 200
                AjaxHelpers.respondWithJson(requests, {});
                
                // Expect that the error is hidden
                expect(view.$'#submission-error').toHaveClass('hidden');
            });
        });
    }
);
