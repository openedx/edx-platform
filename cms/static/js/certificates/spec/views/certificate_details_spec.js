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

    describe('Experiment group configurations details view', function() {
        beforeEach(function() {
            TemplateHelpers.installTemplate('group-configuration-details', true);

            this.model = new GroupConfigurationModel({
                name: 'Configuration',
                description: 'Configuration Description',
                id: 0
            });

            this.collection = new GroupConfigurationCollection([ this.model ]);
            this.collection.outlineUrl = '/outline';
            this.view = new GroupConfigurationDetailsView({
                model: this.model
            });
            appendSetFixtures(this.view.render().el);
        });

        it('should render properly', function() {
            assertTheDetailsView(this.view, 'Configuration');
        });

        it('should show groups appropriately', function() {
            this.model.get('groups').add([{}]);
            this.model.set('showGroups', false);
            this.view.$('.show-groups').click();

            expect(this.model.get('showGroups')).toBeTruthy();
            expect(this.view.$(SELECTORS.group).length).toBe(3);
            expect(this.view.$(SELECTORS.groupsCount)).not.toExist();
            expect(this.view.$(SELECTORS.description))
                .toContainText('Configuration Description');
            expect(this.view.$(SELECTORS.groupsAllocation))
                .toContainText('33%');
        });

        it('should hide groups appropriately', function() {
            this.model.get('groups').add([{}]);
            this.model.set('showGroups', true);
            this.view.$('.hide-groups').click();

            expect(this.model.get('showGroups')).toBeFalsy();
            expect(this.view.$(SELECTORS.group)).not.toExist();
            expect(this.view.$(SELECTORS.groupsCount))
                .toContainText('Contains 3 groups');
            expect(this.view.$(SELECTORS.description)).not.toExist();
            expect(this.view.$(SELECTORS.groupsAllocation)).not.toExist();
        });

        it('should show empty usage appropriately', function() {
            this.model.set('showGroups', false);
            this.view.$('.show-groups').click();
            assertShowEmptyUsages(
                this.view,
                'This Group Configuration is not in use. ' +
                'Start by adding a content experiment to any Unit via the'
            );
        });

        it('should hide empty usage appropriately', function() {
            this.model.set('showGroups', true);
            this.view.$('.hide-groups').click();
            assertHideEmptyUsages(this.view)
        });

        it('should show non-empty usage appropriately', function() {
            setUsageInfo(this.model);
            this.model.set('showGroups', false);
            this.view.$('.show-groups').click();

            assertShowNonEmptyUsages(
                this.view,
                'This Group Configuration is used in:',
                'Cannot delete when in use by an experiment'
            )
        });

        it('should hide non-empty usage appropriately', function() {
            setUsageInfo(this.model);
            this.model.set('showGroups', true);
            this.view.$('.hide-groups').click();

            expect(this.view.$(SELECTORS.note)).toHaveAttr(
                'data-tooltip', 'Cannot delete when in use by an experiment'
            );
            assertHideNonEmptyUsages(this.view);
        });

        it('should show validation warning icon and message appropriately', function() {
            this.model.set('usage', [
                {
                    'label': 'label1',
                    'url': 'url1',
                    'validation': {
                        'text': "Warning message",
                        'type': 'warning'
                    }
                }
            ]);
            this.model.set('showGroups', false);
            this.view.$('.show-groups').click();

            expect(this.view.$(SELECTORS.usageUnitMessage)).toContainText('Warning message');
            expect(this.view.$(SELECTORS.usageUnitWarningIcon)).toExist();
        });

        it('should show validation error icon and message appropriately', function() {
            this.model.set('usage', [
                {
                    'label': 'label1',
                    'url': 'url1',
                    'validation': {
                        'text': "Error message",
                        'type': 'error'
                    }
                }
            ]);
            this.model.set('showGroups', false);
            this.view.$('.show-groups').click();

            expect(this.view.$(SELECTORS.usageUnitMessage)).toContainText('Error message');
            expect(this.view.$(SELECTORS.usageUnitErrorIcon)).toExist();
        });

        it('should hide validation icons and messages appropriately', function() {
            setUsageInfo(this.model);
            this.model.set('showGroups', true);
            this.view.$('.hide-groups').click();

            assertHideValidationContent(this.view);
        });
    });

    describe('Content groups details view', function() {

        beforeEach(function() {
            TemplateHelpers.installTemplate('content-group-details', true);
            this.model = new GroupModel({name: 'Content Group', id: 0});

            var saveableModel = new GroupConfigurationModel({
                name: 'Content Group Configuration',
                id: 0,
                scheme:'cohort',
                groups: new GroupCollection([this.model]),
            }, {canBeEmpty: true});

            saveableModel.urlRoot = '/mock_url';

            this.collection = new GroupConfigurationCollection([ saveableModel ]);
            this.collection.outlineUrl = '/outline';

            this.view = new ContentGroupDetailsView({
                model: this.model
            });
            appendSetFixtures(this.view.render().el);
        });

        it('should render properly', function() {
            assertTheDetailsView(this.view, 'Content Group');
        });

        it('should show empty usage appropriately', function() {
            this.view.$('.show-groups').click();
            assertShowEmptyUsages(this.view, 'This content group is not in use. ');
        });

        it('should hide empty usage appropriately', function() {
            this.view.$('.hide-groups').click();
            assertHideEmptyUsages(this.view)
        });

        it('should show non-empty usage appropriately', function() {
            setUsageInfo(this.model);
            this.view.$('.show-groups').click();

            assertShowNonEmptyUsages(
                this.view,
                'This content group is used in:',
                'Cannot delete when in use by a unit'
            )
        });

        it('should hide non-empty usage appropriately', function() {
            setUsageInfo(this.model);
            this.view.$('.hide-groups').click();

            expect(this.view.$('li.action-delete')).toHaveAttr(
                'data-tooltip', 'Cannot delete when in use by a unit'
            );
            assertHideNonEmptyUsages(this.view);
        });

        it('should hide validation icons and messages appropriately', function() {
            setUsageInfo(this.model);
            this.view.$('.hide-groups').click();
            assertHideValidationContent(this.view);
        });
    });




});
