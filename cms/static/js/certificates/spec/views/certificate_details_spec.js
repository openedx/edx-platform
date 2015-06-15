// Jasmine Test Suite: Certifiate Details View

define([ // jshint ignore:line
    'underscore',
    'js/models/course',
    'js/certificates/collections/certificates',
    'js/certificates/models/certificate',
    'js/certificates/views/certificate_details',
    'js/certificates/views/certificate_preview',
    'js/views/feedback_notification',
    'common/js/spec_helpers/ajax_helpers',
    'common/js/spec_helpers/template_helpers',
    'js/spec_helpers/view_helpers',
    'js/spec_helpers/validation_helpers',
    'js/certificates/spec/custom_matchers'
],
function(_, Course, CertificatesCollection, CertificateModel, CertificateDetailsView, CertificatePreview,
         Notification, AjaxHelpers, TemplateHelpers, ViewHelpers, ValidationHelpers, CustomMatchers) {
    'use strict';

    var SELECTORS = {
        detailsView: '.certificate-details',
        editView: '.certificate-edit',
        itemView: '.certificates-list-item',
        name: '.certificate-name',
        description: '.certificate-description',
        course_title: '.course-title-override .certificate-value',
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
        window.certWebPreview = new CertificatePreview({
            course_modes: ['honor', 'test'],
            certificate_web_view_url: '/users/1/courses/orgX/009/2016'
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
                    view.$(SELECTORS[selector]).trigger('change');
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
            CustomMatchers(this); // jshint ignore:line
        });

        describe('The Certificate Details view', function() {

            it('should parse a JSON string collection into a Backbone model collection', function () {
                var course_title = "Test certificate course title override 2";
                var CERTIFICATE_JSON = '[{"course_title": "' + course_title + '", "signatories":"[]"}]';
                this.collection.parse(CERTIFICATE_JSON);
                var model = this.collection.at(1);
                expect(model.get('course_title')).toEqual(course_title);
            });

            it('should parse a JSON object collection into a Backbone model collection', function () {
                var course_title = "Test certificate course title override 2";
                var CERTIFICATE_JSON_OBJECT = [{
                    "course_title" : course_title,
                    "signatories" : "[]"
                }];
                this.collection.parse(CERTIFICATE_JSON_OBJECT);
                var model = this.collection.at(1);
                expect(model.get('course_title')).toEqual(course_title);
            });

            it('should have empty certificate collection if there is an error parsing certifcate JSON', function () {
                var CERTIFICATE_INVALID_JSON = '[{"course_title": Test certificate course title override, "signatories":"[]"}]'; // jshint ignore:line
                var collection_length = this.collection.length;
                this.collection.parse(CERTIFICATE_INVALID_JSON);
                //collection length should remain the same since we have error parsing JSON
                expect(this.collection.length).toEqual(collection_length);
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
                expect(this.view.$(SELECTORS.signatory_name_value)).toContainText(/^[A-Za-z\s]{10,40}/);
                expect(this.view.$(SELECTORS.signatory_title_value)).toContainText('Title of the signatory');
                expect(
                    this.view.$(SELECTORS.signatory_organization_value)
                ).toContainText('Organization of the signatory');
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

                setValuesToInputs(this.view, {
                    inputSignatoryTitle: 'New Signatory Test Title'
                });

                setValuesToInputs(this.view, {
                    inputSignatoryOrganization: 'New Signatory Test Organization'
                });

                this.view.$(SELECTORS.signatory_panel_save).click();

                ViewHelpers.verifyNotificationShowing(notificationSpy, /Saving/);
                requests[0].respond(200);
                ViewHelpers.verifyNotificationHidden(notificationSpy);

                expect(this.view.$(SELECTORS.signatory_name_value)).toContainText('New Signatory Test Name');
                expect(this.view.$(SELECTORS.signatory_title_value)).toContainText('New Signatory Test Title');
                expect(
                    this.view.$(SELECTORS.signatory_organization_value)
                ).toContainText('New Signatory Test Organization');
            });
            it('should not allow invalid data when saving changes made during in-line signatory editing', function() {
                this.view.$(SELECTORS.edit_signatory).click();

                setValuesToInputs(this.view, {
                    inputSignatoryName: 'New Signatory Test Name'
                });

                setValuesToInputs(this.view, {
                    inputSignatoryTitle: 'New Signatory Test Title longer than 40 characters in length'
                });

                setValuesToInputs(this.view, {
                    inputSignatoryOrganization: 'New Signatory Test Organization'
                });

                this.view.$(SELECTORS.signatory_panel_save).click();
                expect(this.view.$(SELECTORS.inputSignatoryTitle).parent()).toHaveClass('error');
            });
        });
    });
});
