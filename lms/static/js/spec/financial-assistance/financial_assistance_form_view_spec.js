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
                            {name: 'Verified with Audit', value: 'course-v1:HCFA+VA101+2015'},
                            {name: 'Something Else', value: 'course-v1:SomethingX+SE101+215'},
                            {name: 'Test Course', value: 'course-v1:TestX+T101+2015'}
                        ],
                        placeholder: '',
                        required: true,
                        requiredStr: '',
                        type: 'select'
                    }, {
                        defaultValue: '',
                        instructions: '',
                        label: 'Paying the verified certificate fee for the above course would cause me economic hardship',
                        name: 'certify-economic-hardship',
                        placeholder: '',
                        required: true,
                        restrictions: {},
                        type: 'checkbox'
                    }, {
                        defaultValue: '',
                        instructions: '',
                        label: 'I will work diligently to complete the course work and receive a certificate',
                        name: 'certify-complete-certificate',
                        placeholder: '',
                        required: true,
                        restrictions: {},
                        type: 'checkbox'
                    }, {
                        defaultValue: '',
                        instructions: '',
                        label: 'I have read, understand, and will abide by the Honor Code for the edX Site',
                        name: 'certify-honor-code',
                        placeholder: '',
                        required: true,
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
                course_id: 'course-v1:edX+Test+1',
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

            view.$('#financial-assistance-course').val(courseSelectValue);
            view.$('#financial-assistance-certify-economic-hardship').prop('checked', true );
            view.$('#financial-assistance-certify-complete-certificate').prop('checked', true );
            view.$('#financial-assistance-certify-honor-code').prop('checked', true );
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

        failedSubmission = function(statusCode) {
            expect(view.$('.js-success-message').length).toEqual(0);
            expect(view.$formFeedback.find('.' + view.formErrorsJsHook).length).toEqual(0);
            validSubmission();
            view.model.trigger('error', {status: statusCode});
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
            expect($form.find('input[type=checkbox]')[0].name).toEqual(context.fields[1].name);
            expect($form.find('input[type=checkbox]')[1].name).toEqual(context.fields[2].name);
            expect($form.find('input[type=checkbox]')[2].name).toEqual(context.fields[3].name);
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
            failedSubmission(500);
        });

        it('should submit the form and show an error message if content is valid and API returns 403 error', function() {
            failedSubmission(403);
            expect(view.$('.message-copy').text()).toContain('You must confirm your email');
        });

        it('should allow form resubmission after a front end validation failure', function() {
            view.$('#financial-assistance-course').val('');
            expect(view.model.save).not.toHaveBeenCalled();
            validSubmission();
        });

        it('should allow form resubmission after an API error is returned', function() {
            failedSubmission(500);
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
