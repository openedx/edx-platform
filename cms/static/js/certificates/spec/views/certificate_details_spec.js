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
        note: '.wrapper-delete-button'
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

    describe('Experiment certificates details view', function() {
        beforeEach(function() {
            TemplateHelpers.installTemplate('certificate-details', true);

            this.model = new CertificateModel({
                id: 0,
                name: 'Test Name',
                description: 'Test Description'
            });

            this.collection = new CertificatesCollection([ this.model ]);
            this.collection.certificateUrl = '/certificates/edX/DemoX/Demo_Course';
            this.view = new CertificateDetailsView({
                model: this.model
            });
            appendSetFixtures(this.view.render().el);
            CustomMatchers(this);
        });

        it('JSON collection parsing into model', function () {
            var CERTIFICATE_JSON = '[{"name": "Test certificate name", "description": "Test certificate description"}]';
            this.collection.parse(CERTIFICATE_JSON);
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
            this.view.$('.hide-details').click();

            // The "Certificate Description" field should be hidden.
            expect(this.view.$(SELECTORS.description)).not.toExist();
        });
    });
});
