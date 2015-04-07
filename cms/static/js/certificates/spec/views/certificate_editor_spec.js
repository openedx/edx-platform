// Jasmine Test Suite: Certifiate Editor View

define([
    'underscore', 'js/models/course',
    'js/certificates/models/certificate',
    'js/certificates/collections/certificates',
    'js/certificates/views/certificate_editor',
    'js/views/feedback_notification',
    'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
    'js/spec_helpers/view_helpers', 'js/spec_helpers/validation_helpers', 'js/certificates/spec/custom_matchers',
    'jasmine-stealth'
], function(
    _, Course, CertificateModel, CertificatesCollection, CertificateEditorView,
    Notification, AjaxHelpers, TemplateHelpers, ViewHelpers, ValidationHelpers, CustomMatchers
) {
    'use strict';

    var SELECTORS = {
        detailsView: '.certificate-details',
        editView: '.certificate-edit',
        itemView: '.certificates-list-item',
        name: '.certificate-name',
        description: '.certificate-description',
        errorMessage: '.certificate-edit-error',
        inputCertificateName: '.collection-name-input',
        inputCertificateDescription: '.certificate-description-input',
        warningMessage: '.certificate-validation-text',
        warningIcon: '.wrapper-certificate-validation > i',
        note: '.wrapper-delete-button'
    };

    var submitForm = function (view, requests, notificationSpy) {
        view.$('form').submit();
        ViewHelpers.verifyNotificationShowing(notificationSpy, /Saving/);
    };

    var submitAndVerifyFormError = function (view, requests, notificationSpy) {
            view.$('form').submit();
            ViewHelpers.verifyNotificationShowing(notificationSpy, /Saving/);
            AjaxHelpers.respondWithError(requests);
            ViewHelpers.verifyNotificationShowing(notificationSpy, /Saving/);
        };


    beforeEach(function() {
        window.course = new Course({
            id: '5',
            name: 'Course Name',
            url_name: 'course_name',
            org: 'course_org',
            num: 'course_num',
            revision: 'course_rev'
        });


    });

    afterEach(function() {
        delete window.course;
    });

    describe('Experiment certificate editor view', function() {
        var setValuesToInputs = function (view, values) {
            _.each(values, function (value, selector) {
                if (SELECTORS[selector]) {
                    view.$(SELECTORS[selector]).val(value);
                }
            });
        };

        beforeEach(function() {
            ViewHelpers.installViewTemplates();
            TemplateHelpers.installTemplate('certificate-editor', true);

             this.model = new CertificateModel({
                id: 0,
                name: 'Test Name',
                description: 'Test Description'
            });

            this.collection = new CertificatesCollection();
            this.collection.add(this.model);
            this.collection.url = '/certificates/edX/DemoX/Demo_Course';
            this.view = new CertificateEditorView({
                model: this.model

            });
            appendSetFixtures(this.view.render().el);
            CustomMatchers(this);
        });

        describe('Basic', function () {
            it('can render properly', function() {
                expect(this.view.$("[name='certificate-name']").val()).toBe('Test Name')
                expect(this.view.$("[name='certificate-description']").val()).toBe('Test Description')
                expect(this.view.$('.action-delete')).toExist();
            });

            it('should save properly', function() {
                var requests = AjaxHelpers.requests(this),
                    notificationSpy = ViewHelpers.createNotificationSpy();
                this.view.$('.action-add').click();

                setValuesToInputs(this.view, {
                    inputCertificateName: 'New Test Name',
                    inputCertificateDescription: 'New Test Description'
                });

                submitForm(this.view, requests, notificationSpy);
                expect(this.model).toBeCorrectValuesInModel({
                    name: 'New Test Name',
                    description: 'New Test Description'
                });
            });

            it('does not hide saving message if failure', function() {
                var requests = AjaxHelpers.requests(this),
                    notificationSpy = ViewHelpers.createNotificationSpy();
                this.view.$(SELECTORS.inputCertificateName).val('New Test Name')
                this.view.$(SELECTORS.inputCertificateDescription).val('New Test Description')
                submitAndVerifyFormError(this.view, requests, notificationSpy)
            });

            it('does not save on cancel', function() {
                // When we cancel the action, the model values should be reverted to original state
                // And the model should still be present in the collection
                expect(this.view.$('.action-add'));
                this.view.$('.action-add').click();
                this.view.$(SELECTORS.inputCertificateName).val('New Certificate');
                this.view.$(SELECTORS.inputCertificateDescription).val('New Certificate Description');

                this.view.$('.action-cancel').click();
                expect(this.model).toBeCorrectValuesInModel({
                    name: 'Test Name',
                    description: 'Test Description'
                })
                expect(this.collection.length).toBe(1);
            });
        });
    });
});
