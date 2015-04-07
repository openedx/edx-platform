// Jasmine Test Suite: Certifiate Details View

define([
    'underscore', 'js/models/course',
    'js/certificates/collections/certificates',
    'js/certificates/models/certificate',
    'js/certificates/views/certificate_details',
    'js/views/feedback_notification',
    'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
    'js/spec_helpers/view_helpers', 'js/spec_helpers/validation_helpers',
    'js/certificates/spec/custom_matchers', 'jasmine-stealth'
], function(
    _, Course, CertificatesCollection, CertificateModel, CertificateDetailsView,
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
        inputName: '.collection-name-input',
        inputDescription: '.certificate-description-input',
        warningMessage: '.certificate-validation-text',
        warningIcon: '.wrapper-certificate-validation > i',
        note: '.wrapper-delete-button',
        signatory_name_value: '.signatory-name-value',
        signatory_title_value: '.signatory-title-value',
        signatory_organization_value: '.signatory-organization-value',
        edit_signatory: '.edit-signatory',
        signatory_panel_save: '.signatory-panel-save',
        signatory_panel_close: '.signatory-panel-close',
        inputSignatoryName: '.signatory-name-input',
        inputSignatoryTitle: '.signatory-title-input',
        inputSignatoryOrganization: '.signatory-organization-input'
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

    describe('Certificate details views', function() {
        var setValuesToInputs = function (view, values) {
            _.each(values, function (value, selector) {
                if (SELECTORS[selector]) {
                    view.$(SELECTORS[selector]).val(value);
                }
            });
        };

        beforeEach(function() {
            TemplateHelpers.installTemplates(['certificate-details', 'signatory-details', 'signatory-editor'], true);

            this.newModelOptions = {add: true};
            this.model = new CertificateModel({
                name: 'Test Name',
                description: 'Test Description'

            }, this.newModelOptions);

            this.collection = new CertificatesCollection([ this.model ], {
                certificateUrl: '/certificates/'+ window.course.id
            });
            this.model.set('id', 0);
            this.view = new CertificateDetailsView({
                model: this.model
            });
            appendSetFixtures(this.view.render().el);
            CustomMatchers(this);
        });

        describe('Certificate details view', function() {

            it('JSON string collection parsing into model', function () {
                var CERTIFICATE_JSON = '[{"name": "Test certificate name", "description": "Test certificate description", "signatories":"[]"}]';
                this.collection.parse(CERTIFICATE_JSON);
                var model = this.collection.at(1);
                expect(model.get('name')).toEqual('Test certificate name');
                expect(model.get('description')).toEqual('Test certificate description');
            });

            it('JSON object collection parsing into model', function () {
                var CERTIFICATE_JSON_OBJECT = [{"name": "Test certificate name", "description": "Test certificate description", "signatories":"[]"}];
                this.collection.parse(CERTIFICATE_JSON_OBJECT);
                var model = this.collection.at(1);
                expect(model.get('name')).toEqual('Test certificate name');
                expect(model.get('description')).toEqual('Test certificate description');
            });

            it('should render properly', function () {
                expect(this.view.$el).toContainText('Test Name');
                expect(this.view.$('.delete')).toExist();
                expect(this.view.$('.edit')).toExist();
            });

            it('can edit certificate', function(){
                this.view.$('.edit').click();
                // The Certificate Model should be in 'edit' mode
                expect(this.model.get('editing')).toBe(true);
            });

            it('show certificate details', function(){
                this.view.$('.show-details').click();

                // The "Certificate Description" field should be visible.
                expect(this.view.$(SELECTORS.description)).toContainText('Test Description');
            });


            it('hide certificate details', function(){
                this.view.render(true);
                this.view.$('.hide-details').click();

                // The "Certificate Description" field should be hidden.
                expect(this.view.$(SELECTORS.description)).not.toExist();
            });

        });

        describe('Signatory details view', function(){

            beforeEach(function() {
                this.view.render(true);
            });

            it('can edit signatory on its own', function() {

                this.view.$(SELECTORS.edit_signatory).click();
                expect(this.view.$(SELECTORS.inputSignatoryName)).toExist();
                expect(this.view.$(SELECTORS.inputSignatoryTitle)).toExist();
                expect(this.view.$(SELECTORS.inputSignatoryOrganization)).toExist();
            });

            it('signatory saved successfully after editing', function() {

                var requests = AjaxHelpers.requests(this),
                    notificationSpy = ViewHelpers.createNotificationSpy();

                this.view.$(SELECTORS.edit_signatory).click();

                setValuesToInputs(this.view, {
                    inputSignatoryName: 'New Signatory Test Name'
                });
                this.view.$(SELECTORS.inputSignatoryName).trigger('change');

                setValuesToInputs(this.view, {
                    inputSignatoryTitle: 'New Signatory Test Title'
                });
                this.view.$(SELECTORS.inputSignatoryTitle).trigger('change');

                setValuesToInputs(this.view, {
                    inputSignatoryOrganization: 'New Signatory Test Organization'
                });
                this.view.$(SELECTORS.inputSignatoryOrganization).trigger('change');
                this.view.$(SELECTORS.signatory_panel_save).click();

                ViewHelpers.verifyNotificationShowing(notificationSpy, /Saving/);
                requests[0].respond(200);
                ViewHelpers.verifyNotificationHidden(notificationSpy);

                expect(this.view.$(SELECTORS.signatory_name_value)).toContainText('New Signatory Test Name');
                expect(this.view.$(SELECTORS.signatory_title_value)).toContainText('New Signatory Test Title');
                expect(this.view.$(SELECTORS.signatory_organization_value)).toContainText('New Signatory Test Organization');
            });

            it('show certificate signatories details', function(){
                this.view.$('.show-details').click();

                // The default certificate signatory should be visible.
                expect(this.view.$(SELECTORS.signatory_name_value)).toContainText('Name of the signatory');
                expect(this.view.$(SELECTORS.signatory_title_value)).toContainText('Title of the signatory');
                expect(this.view.$(SELECTORS.signatory_organization_value)).toContainText('Organization of the signatory');
            });
        });
    });
});
