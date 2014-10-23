define(['js/common_helpers/template_helpers', 'js/student_account/views/PasswordResetView'],
    function(TemplateHelpers) {
        describe('edx.student.account.PasswordResetView', function() {
            'use strict';

            var view = null,
                ajaxSuccess = true;

            var submitEmail = function(validationSuccess) {
                // Simulate manual entry of an email address
                $('#reset-password-email').val('foo@bar.baz');

                // Create a fake click event
                var clickEvent = $.Event('click');

                // Used to avoid spying on view.validate twice
                if (typeof validationSuccess !== 'undefined') {
                    // Force validation to return as expected
                    spyOn(view, 'validate').andReturn(validationSuccess);
                }

                // Submit the email address
                view.submitForm(clickEvent);
            };

            var assertAjax = function(url, method, data) {
                expect($.ajax).toHaveBeenCalled();
                var ajaxArgs = $.ajax.mostRecentCall.args[0];
                expect(ajaxArgs.url).toEqual(url);
                expect(ajaxArgs.type).toEqual(method);
                expect(ajaxArgs.data).toEqual(data)
                expect(ajaxArgs.headers.hasOwnProperty("X-CSRFToken")).toBe(true);
            };

            beforeEach(function() {
                setFixtures("<div id='password-reset-wrapper'></div>");
                TemplateHelpers.installTemplate('templates/student_account/password_reset');
                TemplateHelpers.installTemplate('templates/student_account/form_field');

                // Stub AJAX calls
                spyOn($, 'ajax').andCallFake(function() {
                    return $.Deferred(function(defer) {
                        if (ajaxSuccess) {
                            defer.resolve();
                        } else {
                            defer.reject();
                        }
                    }).promise();
                });

                view = new edx.student.account.PasswordResetView();
            });

            it("allows the user to request a new password", function() {
                submitEmail(true);
                assertAjax('/account/password', 'POST', {email: 'foo@bar.baz'});
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

            it("displays an error if the server could not be contacted", function() {
                // If we get an error status on the AJAX request, display an error
                ajaxSuccess = false;
                submitEmail(true);
                expect(view.$resetFail).not.toHaveClass('hidden');

                // If we try again and succeed, the error should go away
                ajaxSuccess = true;
                // No argument means we won't spy on view.validate again
                submitEmail();
                expect(view.$resetFail).toHaveClass('hidden');
            });
        });
    }
);
