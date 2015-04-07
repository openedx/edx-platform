define([
    'underscore', 'js/models/course',
    'js/certificates/collections/certificates',
    'js/certificates/models/certificate',
    'js/certificates/views/certificate_details',
    'js/certificates/views/certificate_editor',
    'js/certificates/views/certificate_item',
    'js/certificates/views/certificates_list',
    'js/views/feedback_notification',
    'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
    'js/spec_helpers/view_helpers', 'js/spec_helpers/assertion_helpers', 'js/spec_helpers/validation_helpers'
    'jasmine-stealth'
], function(
    _, Course, CertificateModel, CertificatesCollection,
    CertificateDetailsView, CertificatesListView, CertificateEditorView, CertificateItemView,
    Notification, AjaxHelpers, TemplateHelpers, ViewHelpers, ValidationHelpers
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

        this.addMatchers({
            toContainText: function(text) {
                var trimmedText = $.trim(this.actual.text());

                if (text && $.isFunction(text.test)) {
                    return text.test(trimmedText);
                } else {
                    return trimmedText.indexOf(text) !== -1;
                }
            },
            toBeCorrectValuesInInputs: function (values) {
                var expected = {
                    name: this.actual.$(SELECTORS.inputName).val(),
                    description: this.actual
                        .$(SELECTORS.inputDescription).val()
                };

                return _.isEqual(values, expected);
            },
            toBeCorrectValuesInModel: function (values) {
                return _.every(values, function (value, key) {
                    return this.actual.get(key) === value;
                }.bind(this));
            },
            toHaveDefaultNames: function (values) {
                var actualValues = $.map(this.actual, function (item) {
                    return $(item).val();
                });

                return _.isEqual(actualValues, values);
            }
        });
    });

    afterEach(function() {
        delete window.course;
    });

    describe('Experiment group configurations group editor view', function() {
        beforeEach(function() {
            TemplateHelpers.installTemplate('group-edit', true);

            this.model = new GroupModel({
                name: 'Group A'
            });

            this.collection = new GroupCollection([this.model]);

            this.view = new ExperimentGroupEditView({
                model: this.model
            });
        });

        describe('Basic', function () {
            it('can render properly', function() {
                this.view.render();
                expect(this.view.$('.group-name').val()).toBe('Group A');
                expect(this.view.$('.group-allocation')).toContainText('100%');
            });

            it ('can delete itself', function() {
                this.view.render().$('.action-close').click();
                expect(this.collection.length).toEqual(0);
            });
        });
    });

    describe('Experiment group configurations group editor view', function() {
        beforeEach(function() {
            TemplateHelpers.installTemplate('group-edit', true);

            this.model = new GroupModel({
                name: 'Group A'
            });

            this.collection = new GroupCollection([this.model]);

            this.view = new ExperimentGroupEditView({
                model: this.model
            });
        });

        describe('Basic', function () {
            it('can render properly', function() {
                this.view.render();
                expect(this.view.$('.group-name').val()).toBe('Group A');
                expect(this.view.$('.group-allocation')).toContainText('100%');
            });

            it ('can delete itself', function() {
                this.view.render().$('.action-close').click();
                expect(this.collection.length).toEqual(0);
            });
        });


    describe('Content groups editor view', function() {

        beforeEach(function() {
            ViewHelpers.installViewTemplates();
            TemplateHelpers.installTemplates(['content-group-editor']);

            this.model = new GroupModel({name: 'Content Group', id: 0});

            this.saveableModel = new GroupConfigurationModel({
                name: 'Content Group Configuration',
                id: 0,
                scheme:'cohort',
                groups: new GroupCollection([this.model]),
                editing:true
            });

            this.collection = new GroupConfigurationCollection([ this.saveableModel ]);
            this.collection.outlineUrl = '/outline';
            this.collection.url = '/group_configurations';

            this.view = new ContentGroupEditorView({
                model: this.model
            });
            appendSetFixtures(this.view.render().el);
        });

        it('should save properly', function() {
            var requests = AjaxHelpers.requests(this),
                notificationSpy = ViewHelpers.createNotificationSpy();

            this.view.$('.action-add').click();
            this.view.$(SELECTORS.inputName).val('New Content Group');

            submitAndVerifyFormSuccess(this.view, requests, notificationSpy);

            expect(this.model).toBeCorrectValuesInModel({
                name: 'New Content Group'
            });
            expect(this.view.$el).not.toExist();
        });

        it('does not hide saving message if failure', function() {
            var requests = AjaxHelpers.requests(this),
                notificationSpy = ViewHelpers.createNotificationSpy();
            this.view.$(SELECTORS.inputName).val('New Content Group')

            submitAndVerifyFormError(this.view, requests, notificationSpy)
        });

        it('does not save on cancel', function() {
            expect(this.view.$('.action-add'));
            this.view.$('.action-add').click();
            this.view.$(SELECTORS.inputName).val('New Content Group');

            this.view.$('.action-cancel').click();
            expect(this.model).toBeCorrectValuesInModel({
                name: 'Content Group',
            });
            // Model is still exist in the collection
            expect(this.collection.indexOf(this.saveableModel)).toBeGreaterThan(-1);
            expect(this.collection.length).toBe(1);
        });

        it('cannot be deleted if it is in use', function () {
            assertCannotDeleteUsed(
                this,
                'Cannot delete when in use by a unit',
                'This content group is used in one or more units.'
            );
        });

        it('does not contain warning message if it is not in use', function () {
            assertUnusedOptions(this);
        });
    });


    });
});
