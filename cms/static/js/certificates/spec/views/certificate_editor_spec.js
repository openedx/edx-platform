// Jasmine Test Suite: Certifiate Editor View

define([
    'underscore', 'js/models/course',
    'js/certificates/models/certificate',
    'js/certificates/models/signatory',
    'js/certificates/collections/certificates',
    'js/certificates/views/certificate_editor',
    'js/views/feedback_notification',
    'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
    'js/spec_helpers/view_helpers', 'js/spec_helpers/validation_helpers', 'js/certificates/spec/custom_matchers',
    'jasmine-stealth'
], function(
    _, Course, CertificateModel, SignatoryModel, CertificatesCollection, CertificateEditorView,
    Notification, AjaxHelpers, TemplateHelpers, ViewHelpers, ValidationHelpers, CustomMatchers
) {
    'use strict';

    var MAX_SIGNATORIES = 4;
    var SELECTORS = {
        detailsView: '.certificate-details',
        editView: '.certificate-edit',
        itemView: '.certificates-list-item',
        name: '.certificate-name',
        description: '.certificate-description',
        errorMessage: '.certificate-edit-error',
        inputCertificateName: '.collection-name-input',
        inputCertificateDescription: '.certificate-description-input',
        inputSignatoryName: '.signatory-name-input',
        inputSignatoryTitle: '.signatory-title-input',
        inputSignatoryOrganization: '.signatory-organization-input',
        warningMessage: '.certificate-validation-text',
        warningIcon: '.wrapper-certificate-validation > i',
        note: '.wrapper-delete-button',
        action_add_signatory: '.action-add-signatory',
        signatory_panel_delete: '.signatory-panel-delete'
    };

    var submitForm = function (view, requests, notificationSpy) {
        view.$('form').submit();
        ViewHelpers.verifyNotificationShowing(notificationSpy, /Saving/);
        requests[0].respond(200);
        ViewHelpers.verifyNotificationHidden(notificationSpy);
    };

    var submitAndVerifyFormError = function (view, requests, notificationSpy) {
            view.$('form').submit();
            ViewHelpers.verifyNotificationShowing(notificationSpy, /Saving/);
            AjaxHelpers.respondWithError(requests);
            ViewHelpers.verifyNotificationShowing(notificationSpy, /Saving/);
    };

    var clickDeleteItem = function (that, promptText, element) {
        var requests = AjaxHelpers.requests(that),
            promptSpy = ViewHelpers.createPromptSpy(),
            notificationSpy = ViewHelpers.createNotificationSpy();
        that.view.$(element).click();

        ViewHelpers.verifyPromptShowing(promptSpy, promptText);
        ViewHelpers.confirmPrompt(promptSpy);
        ViewHelpers.verifyPromptHidden(promptSpy);
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

    describe('Certificate editor view', function() {
        var setValuesToInputs = function (view, values) {
            _.each(values, function (value, selector) {
                if (SELECTORS[selector]) {
                    view.$(SELECTORS[selector]).val(value);
                }
            });
        };

        beforeEach(function() {
            TemplateHelpers.installTemplates(['certificate-editor', 'signatory-editor'], true);

            this.newModelOptions = {add: true};
            this.model = new CertificateModel({
                name: 'Test Name',
                description: 'Test Description'

            }, this.newModelOptions);

            this.collection = new CertificatesCollection([ this.model ], {
                certificateUrl: '/certificates/'+ window.course.id
            });
            this.model.set('id', 0);
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
                });
                expect(this.collection.length).toBe(1);
            });

            it('user can only add signatories up to max 4', function() {
                for(var i = 1; i < MAX_SIGNATORIES ; i++) {
                    this.view.$(SELECTORS.action_add_signatory).click();
                }
                expect(this.view.$(SELECTORS.action_add_signatory)).toHaveClass('disableClick');

            });

            it('user can add signatories if not reached the upper limit', function() {
                spyOnEvent(SELECTORS.action_add_signatory, 'click');
                this.view.$(SELECTORS.action_add_signatory).click();
                expect('click').not.toHaveBeenPreventedOn(SELECTORS.action_add_signatory);
                expect(this.view.$(SELECTORS.action_add_signatory)).not.toHaveClass('disableClick');
            });

            it('user can add signatories when signatory reached the upper limit But after deleting a signatory',
                function() {
                    for(var i = 1; i < MAX_SIGNATORIES ; i++) {
                        this.view.$(SELECTORS.action_add_signatory).click();
                    }
                    expect(this.view.$(SELECTORS.action_add_signatory)).toHaveClass('disableClick');

                    // now delete anyone of the signatory, Add signatory should be enabled.
                    var signatory = this.model.get('signatories').at(0);
                    var text = 'Are you sure you want to delete "'+ signatory.get('title') +'" as a signatory?';
                    clickDeleteItem(this, text, SELECTORS.signatory_panel_delete + ':first');
                    expect(this.view.$(SELECTORS.action_add_signatory)).not.toHaveClass('disableClick');
                }
            );

            it('signatories should save properly', function() {
                var requests = AjaxHelpers.requests(this),
                    notificationSpy = ViewHelpers.createNotificationSpy();
                this.view.$('.action-add').click();

                setValuesToInputs(this.view, {
                    inputCertificateName: 'New Test Name'
                });

                setValuesToInputs(this.view, {
                    inputCertificateDescription: 'New Test Description'
                });

                setValuesToInputs(this.view, {
                    inputSignatoryName: 'New Signatory Name'
                });
                this.view.$(SELECTORS.inputSignatoryName).trigger('change');

                setValuesToInputs(this.view, {
                    inputSignatoryTitle: 'New Signatory Title'
                });
                this.view.$(SELECTORS.inputSignatoryTitle).trigger('change');

                setValuesToInputs(this.view, {
                    inputSignatoryOrganization: 'New Signatory Organization'
                });
                this.view.$(SELECTORS.inputSignatoryOrganization).trigger('change');

                submitForm(this.view, requests, notificationSpy);
                expect(this.model).toBeCorrectValuesInModel({
                    name: 'New Test Name',
                    description: 'New Test Description'
                });

                // get the first signatory from the signatories collection.
                var signatory = this.model.get('signatories').at(0);
                expect(signatory).toBeInstanceOf(SignatoryModel);
                expect(signatory.get('name')).toEqual('New Signatory Name');
                expect(signatory.get('title')).toEqual('New Signatory Title');
                expect(signatory.get('organization')).toEqual('New Signatory Organization');
            });
        });
    });
});
