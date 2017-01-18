define([
    'backbone',
    'jquery',
    'js/financial-assistance/models/financial_assistance_model',
    'js/financial-assistance/views/financial_assistance_form_view'
], function(Backbone, $, FinancialAssistanceModel, FinancialAssistanceFormView) {
    'use strict';
        /* jslint maxlen: 500 */

    describe('Financial Assistance View', function() {
        var view = null,
            context = {
                fields: [
                    {
                        defaultValue: '',
                        form: 'financial-assistance',
                        instructions: 'select a course',
                        label: 'Course',
                        name: 'course',
                        options: [
                                {'name': 'Verified with Audit', 'value': 'course-v1:HCFA+VA101+2015'},
                                {'name': 'Something Else', 'value': 'course-v1:SomethingX+SE101+215'},
                                {'name': 'Test Course', 'value': 'course-v1:TestX+T101+2015'}
                        ],
                        placeholder: '',
                        required: true,
                        requiredStr: '',
                        type: 'select'
                    }, {
                        defaultValue: '',
                        instructions: 'Specify your annual income in USD.',
                        label: 'Annual Income',
                        name: 'income',
                        options: [
                                {'name': 'Less than $5,000', 'value': 'Less than $5,000'},
                                {'name': '$5,000 - $10,000', 'value': '$5,000 - $10,000'},
                                {'name': '$10,000 - $15,000', 'value': '$10,000 - $15,000'},
                                {'name': '$15,000 - $20,000', 'value': '$15,000 - $20,000'},
                                {'name': '$20,000 - $25,000', 'value': '$20,000 - $25,000'}
                        ],
                        placeholder: '',
                        required: true,
                        type: 'select'
                    }, {
                        defaultValue: '',
                        instructions: 'Your response should contain approximately 250 - 500 words.',
                        label: 'Tell us about your current financial situation, including any unusual circumstances.',
                        name: 'reason_for_applying',
                        placeholder: '',
                        required: true,
                        restrictions: {
                            min_length: 800,
                            max_length: 2500
                        },
                        type: 'textarea'
                    }, {
                        defaultValue: '',
                        instructions: 'Use between 250 and 500 words or so in your response.',
                        label: 'Tell us about your learning or professional goals. How will a Verified Certificate in this course help you achieve these goals?',
                        name: 'goals',
                        placeholder: '',
                        required: true,
                        restrictions: {
                            min_length: 800,
                            max_length: 2500
                        },
                        type: 'textarea'
                    }, {
                        defaultValue: '',
                        instructions: 'Use between 250 and 500 words or so in your response.',
                        label: 'Tell us about your plans for this course. What steps will you take to help you complete the course work a receive a certificate?',
                        name: 'effort',
                        placeholder: '',
                        required: true,
                        restrictions: {
                            min_length: 800,
                            max_length: 2500
                        },
                        type: 'textarea'
                    }, {
                        defaultValue: '',
                        instructions: 'Annual income and personal information such as email address will not be shared.',
                        label: 'I allow edX to use the information provided in this application for edX marketing purposes.',
                        name: 'mktg-permission',
                        placeholder: '',
                        required: false,
                        restrictions: {},
                        type: 'checkbox'
                    }
                ],
                user_details: {
                    country: 'UK',
                    email: 'xsy@edx.org',
                    name: 'xsy',
                    username: 'xsy4ever'
                },
                header_text: ['Line one.', 'Line two.'],
                student_faq_url: '/faqs',
                dashboard_url: '/dashboard',
                platform_name: 'edx',
                submit_url: '/api/financial/v1/assistance'
            },
            completeForm,
            validSubmission,
            successfulSubmission,
            failedSubmission,
            invalidCountry,
            validCountry;

        completeForm = function() {
            var courseOptions = context.fields[0].options,
                courseSelectValue = courseOptions[courseOptions.length - 1].value;
            var incomeOptions = context.fields[1].options,
                incomeSelectValue = incomeOptions[incomeOptions.length - 1].value;

            view.$('#financial-assistance-course').val(courseSelectValue);
            view.$('#financial-assistance-income').val(incomeSelectValue);
            view.$('textarea').html(Array(802).join('w'));
        };

        validSubmission = function() {
            completeForm();
            view.$('.js-submit-form').click();
            expect(view.model.save).toHaveBeenCalled();
        };

        successfulSubmission = function() {
            expect(view.$('.js-success-message').length).toEqual(0);
            validSubmission();
            view.model.trigger('sync');
            expect(view.$('.js-success-message').length).toEqual(1);
        };

        failedSubmission = function() {
            expect(view.$('.js-success-message').length).toEqual(0);
            expect(view.$formFeedback.find('.' + view.formErrorsJsHook).length).toEqual(0);
            validSubmission();
            view.model.trigger('error', {status: 500});
            expect(view.$('.js-success-message').length).toEqual(0);
            expect(view.$formFeedback.find('.' + view.formErrorsJsHook).length).toEqual(1);
        };

        invalidCountry = function() {
            expect(view.$('.js-success-message').length).toEqual(0);
            expect(view.$formFeedback.find('.' + view.formErrorsJsHook).length).toEqual(1);
            expect(view.$('#user-country-title')).toHaveClass('error');
            expect(view.$('.js-submit-form').prop('disabled')).toBeTruthy();
        };

        validCountry = function() {
            expect(view.$('.js-success-message').length).toEqual(0);
            expect(view.$formFeedback.find('.' + view.formErrorsJsHook).length).toEqual(0);
            expect(view.$('#user-country-title')).not.toHaveClass('error');
            expect(view.$('.js-submit-form').prop('disabled')).toBeFalsy();
        };

        beforeEach(function() {
            setFixtures('<div class="financial-assistance-wrapper"></div>');

            spyOn(FinancialAssistanceModel.prototype, 'save');

            view = new FinancialAssistanceFormView({
                el: '.financial-assistance-wrapper',
                context: context
            });
        });

        afterEach(function() {
            view.undelegateEvents();
            view.remove();
        });

        it('should exist', function() {
            expect(view).toBeDefined();
        });

        it('should load the form based on passed in context', function() {
            var $form = view.$('.financial-assistance-form');

            expect($form.find('select').first().attr('name')).toEqual(context.fields[0].name);
            expect($form.find('select').last().attr('name')).toEqual(context.fields[1].name);
            expect($form.find('textarea').first().attr('name')).toEqual(context.fields[2].name);
            expect($form.find('input[type=checkbox]').attr('name')).toEqual(context.fields[5].name);
        });

        it('should not submit the form if the front end validation fails', function() {
            expect(view.$formFeedback.find('.' + view.formErrorsJsHook).length).toEqual(0);
            view.$('.js-submit-form').click();
            expect(view.model.save).not.toHaveBeenCalled();
            expect(view.$formFeedback.find('.' + view.formErrorsJsHook).length).toEqual(1);
        });

        it('should submit the form data and additional data if validation passes', function() {
            validSubmission();
        });

        it('should submit the form and show a success message if content is valid and API returns success', function() {
            successfulSubmission();
        });

        it('should submit the form and show an error message if content is valid and API returns error', function() {
            failedSubmission();
        });

        it('should allow form resubmission after a front end validation failure', function() {
            view.$('#financial-assistance-income').val(1312);
            expect(view.model.save).not.toHaveBeenCalled();
            validSubmission();
        });

        it('should allow form resubmission after an API error is returned', function() {
            failedSubmission();
            successfulSubmission();
        });

        it('renders with valid country', function() {
            validCountry();
        });

        describe('when no country', function() {
            beforeEach(function() {
                context.user_details.country = '';

                view = new FinancialAssistanceFormView({
                    el: '.financial-assistance-wrapper',
                    context: context
                });
            });

            it('renders invalid country', function() {
                invalidCountry();
            });
        });
    });
}
);
