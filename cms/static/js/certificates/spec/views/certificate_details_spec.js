// Jasmine Test Suite: Certifiate Details View

define([
    'underscore',
    'js/models/course',
    'js/certificates/collections/certificates',
    'js/certificates/models/certificate',
    'js/certificates/views/certificate_details',
    'js/views/feedback_notification',
    'js/common_helpers/ajax_helpers',
    'js/common_helpers/template_helpers',
    'js/spec_helpers/view_helpers',
    'js/spec_helpers/validation_helpers',
    'js/certificates/spec/custom_matchers',
    'jasmine-stealth'
],
function(_, Course, CertificatesCollection, CertificateModel, CertificateDetailsView,
         Notification, AjaxHelpers, TemplateHelpers, ViewHelpers, ValidationHelpers, CustomMatchers) {
    'use strict';

    var SELECTORS = {
        detailsView: '.certificate-details',
        editView: '.certificate-edit',
        itemView: '.certificates-list-item',
        name: '.certificate-name',
        description: '.certificate-description',
        course_title: '.certificate-course-title',
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

    describe('Certificate Details Spec:', function() {
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
                description: 'Test Description',
                course_title: 'Test Course Title Override'

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

        describe('The Certificate Details view', function() {

            it('should parse a JSON string collection into a Backbone model collection', function () {
                var CERTIFICATE_JSON = '[{"name": "Test certificate name", "description": "Test certificate description", "course_title":"Test certificate course title override", "signatories":"[]"}]';
                this.collection.parse(CERTIFICATE_JSON);
                var model = this.collection.at(1);
                expect(model.get('name')).toEqual('Test certificate name');
                expect(model.get('description')).toEqual('Test certificate description');
                expect(model.get('course_title')).toEqual('Test certificate course title override');
            });

            it('should parse a JSON object collection into a Backbone model collection', function () {
                var CERTIFICATE_JSON_OBJECT = [{
                    "name": "Test certificate name 2",
                    "description": "Test certificate description 2",
                    "course_title":"Test certificate course title override 2",
                    "signatories":"[]"
                }];
                this.collection.parse(CERTIFICATE_JSON_OBJECT);
                var model = this.collection.at(1);
                expect(model.get('name')).toEqual('Test certificate name 2');
                expect(model.get('description')).toEqual('Test certificate description 2');
            });

            it('should display the certificate description', function () {
                expect(this.view.$(SELECTORS.description)).toExist();
                console.log(this.view.$(SELECTORS.description).text());
                expect(this.view.$(SELECTORS.description)).toContainText('Test Description');
            });

            it('should display the certificate course title override', function () {
                expect(this.view.$(SELECTORS.course_title)).toExist();
                expect(this.view.$(SELECTORS.course_title)).toContainText('Test Course Title Override');
            });

            it('should present an Edit action', function () {
                expect(this.view.$('.edit')).toExist();
            });

            it('should change to "edit" mode when clicking the Edit button', function(){
                expect(this.view.$('.action-edit .edit')).toExist();
                this.view.$('.action-edit .edit').click();
                expect(this.model.get('editing')).toBe(true);
            });

            it('should present a Delete action', function () {
                expect(this.view.$('.action-delete .delete')).toExist();
            });

            it('should prompt the user when when clicking the Delete button', function(){
                expect(this.view.$('.action-delete .delete')).toExist();
                this.view.$('.action-delete .delete').click();
            });

        });

        describe('Signatory details', function(){

            beforeEach(function() {
                this.view.render(true);
            });

            it('displays certificate signatories details', function(){
                this.view.$('.show-details').click();
                expect(this.view.$(SELECTORS.signatory_name_value)).toContainText('Name of the signatory');
                expect(this.view.$(SELECTORS.signatory_title_value)).toContainText('Title of the signatory');
                expect(this.view.$(SELECTORS.signatory_organization_value)).toContainText('Organization of the signatory');
            });

            it('supports in-line editing of signatory information', function() {

                this.view.$(SELECTORS.edit_signatory).click();
                expect(this.view.$(SELECTORS.inputSignatoryName)).toExist();
                expect(this.view.$(SELECTORS.inputSignatoryTitle)).toExist();
                expect(this.view.$(SELECTORS.inputSignatoryOrganization)).toExist();
            });

            it('correctly persists changes made during in-line signatory editing', function() {

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


        });
    });
});
