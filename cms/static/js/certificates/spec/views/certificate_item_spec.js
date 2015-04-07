// Jasmine Test Suite: Certifiate Item View

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

    describe('Experiment group configurations controller view', function() {

        beforeEach(function() {
            TemplateHelpers.installTemplates([
                'group-configuration-editor', 'group-configuration-details'
            ], true);
            this.model = new GroupConfigurationModel({ id: 0 });
            this.collection = new GroupConfigurationCollection([ this.model ]);
            this.collection.url = '/group_configurations';
            this.view = new GroupConfigurationItemView({
                model: this.model
            });
            appendSetFixtures(this.view.render().el);
        });

        it('should render properly', function() {
            assertControllerView(this.view, SELECTORS.detailsView, SELECTORS.editView);
        });

        it('should destroy itself on confirmation of deleting', function () {
            assertAndDeleteItemError(this, '/group_configurations/0', 'Delete this group configuration?');
        });

        it('does not hide deleting message if failure', function() {
            assertAndDeleteItemWithError(
                this,
                '/group_configurations/0',
                SELECTORS.itemView,
                'Delete this group configuration?'
            );
        });
    });

    describe('Content group controller view', function() {
        beforeEach(function() {
            TemplateHelpers.installTemplates([
                'content-group-editor', 'content-group-details'
            ], true);

            this.model = new GroupModel({name: 'Content Group', id: 0});

            this.saveableModel = new GroupConfigurationModel({
                name: 'Content Group Configuration',
                id: 0,
                scheme:'cohort',
                groups: new GroupCollection([this.model])
            });
            this.saveableModel.urlRoot = '/group_configurations';
            this.collection = new GroupConfigurationCollection([ this.saveableModel ]);
            this.collection.url = '/group_configurations';
            this.view = new ContentGroupItemView({
                model: this.model
            });
            appendSetFixtures(this.view.render().el);
        });

        it('should render properly', function() {
            assertControllerView(this.view, '.content-group-details', '.content-group-edit');
        });

        it('should destroy itself on confirmation of deleting', function () {
            assertAndDeleteItemError(this, '/group_configurations/0/0', 'Delete this content group');
        });

        it('does not hide deleting message if failure', function() {
            assertAndDeleteItemWithError(
                this,
                '/group_configurations/0/0',
                '.content-groups-list-item',
                'Delete this content group'
            );
        });
    });


});
