(function(define) {
    'use strict';
    define([
        'jquery',
        'underscore',
        'common/js/spec_helpers/template_helpers',
        'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'js/student_account/models/AccountRecoveryModel',
        'js/student_account/views/AccountRecoveryView'
    ],
        function($, _, TemplateHelpers, AjaxHelpers, AccountRecoveryModel, AccountRecoveryView) {
            describe('edx.student.account.AccountRecoveryView', function() {
                var model = null,
                    view = null,
                    requests = null,
                    EMAIL = 'xsy@edx.org',
                    FORM_DESCRIPTION = {
                        method: 'post',
                        submit_url: '/account/password',
                        fields: [{
                            name: 'email',
                            label: 'Secondary email',
                            defaultValue: '',
                            type: 'text',
                            required: true,
                            placeholder: 'place@holder.org',
                            instructions: 'Enter your secondary email.',
                            restrictions: {}
                        }]
                    };

                var createAccountRecoveryView = function(that) {
                    // Initialize the account recovery model
                    model = new AccountRecoveryModel({}, {
                        url: FORM_DESCRIPTION.submit_url,
                        method: FORM_DESCRIPTION.method
                    });

                    // Initialize the account recovery view
                    view = new AccountRecoveryView({
                        fields: FORM_DESCRIPTION.fields,
                        model: model
                    });

                    // Spy on AJAX requests
                    requests = AjaxHelpers.requests(that);
                };

                var submitEmail = function(validationSuccess) {
                    // Create a fake click event
                    var clickEvent = $.Event('click');

                    // Simulate manual entry of an email address
                    $('#password-reset-email').val(EMAIL);

                    // If validationSuccess isn't passed, we avoid
                    // spying on `view.validate` twice
                    if (!_.isUndefined(validationSuccess)) {
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
                    setFixtures('<div id="password-reset-form" class="form-wrapper hidden"></div>');
                    TemplateHelpers.installTemplate('templates/student_account/account_recovery');
                    TemplateHelpers.installTemplate('templates/student_account/form_field');
                });

                it('allows the user to request account recovery', function() {
                    var syncSpy, passwordEmailSentSpy;

                    createAccountRecoveryView(this);

                    // We expect these events to be triggered upon a successful account recovery
                    syncSpy = jasmine.createSpy('syncEvent');
                    passwordEmailSentSpy = jasmine.createSpy('passwordEmailSentEvent');
                    view.listenTo(view.model, 'sync', syncSpy);
                    view.listenTo(view, 'account-recovery-email-sent', passwordEmailSentSpy);

                    // Submit the form, with successful validation
                    submitEmail(true);

                    // Verify that the client contacts the server with the expected data
                    AjaxHelpers.expectRequest(
                        requests, 'POST',
                        FORM_DESCRIPTION.submit_url,
                        $.param({email: EMAIL})
                    );

                    // Respond with status code 200
                    AjaxHelpers.respondWithJson(requests, {});

                    // Verify that the events were triggered
                    expect(syncSpy).toHaveBeenCalled();
                    expect(passwordEmailSentSpy).toHaveBeenCalled();

                    // Verify that account recovery view has been removed
                    expect($(view.el).html().length).toEqual(0);
                });

                it('validates the email field', function() {
                    createAccountRecoveryView(this);

                    // Submit the form, with successful validation
                    submitEmail(true);

                    // Verify that validation of the email field occurred
                    expect(view.validate).toHaveBeenCalledWith($('#password-reset-email')[0]);

                    // Verify that no submission errors are visible
                    expect(view.$formFeedback.find('.' + view.formErrorsJsHook).length).toEqual(0);
                });

                it('displays account recovery validation errors', function() {
                    createAccountRecoveryView(this);

                    // Submit the form, with failed validation
                    submitEmail(false);

                    // Verify that submission errors are visible
                    expect(view.$formFeedback.find('.' + view.formErrorsJsHook).length).toEqual(1);
                });

                it('displays error if the server returns an error while sending account recovery email', function() {
                    createAccountRecoveryView(this);
                    submitEmail(true);

                    // Simulate an error from the LMS servers
                    AjaxHelpers.respondWithError(requests);

                    // Expect that an error is displayed
                    expect(view.$formFeedback.find('.' + view.formErrorsJsHook).length).toEqual(1);

                    // If we try again and succeed, the error should go away
                    submitEmail();

                    // This time, respond with status code 200
                    AjaxHelpers.respondWithJson(requests, {});

                    // Expect that the error is hidden
                    expect(view.$formFeedback.find('.' + view.formErrorsJsHook).length).toEqual(0);
                });
            });
        });
}).call(this, define || RequireJS.define);
