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

    describe('Experiment group configurations list view', function() {
        var emptyMessage = 'You have not created any group configurations yet.';

        beforeEach(function() {
            TemplateHelpers.installTemplates(
                ['group-configuration-editor', 'group-edit', 'list']
            );

            this.model = new GroupConfigurationModel({ id: 0 });
            this.collection = new GroupConfigurationCollection();
            this.view = new GroupConfigurationsListView({
                collection: this.collection
            });
            appendSetFixtures(this.view.render().el);
        });

        describe('empty template', function () {
            it('should be rendered if no group configurations', function() {
                expect(this.view.$el).toContainText(emptyMessage);
                expect(this.view.$('.new-button')).toExist();
                expect(this.view.$(SELECTORS.itemView)).not.toExist();
            });

            it('should disappear if group configuration is added', function() {
                expect(this.view.$el).toContainText(emptyMessage);
                expect(this.view.$(SELECTORS.itemView)).not.toExist();
                this.collection.add(this.model);
                expect(this.view.$el).not.toContainText(emptyMessage);
                expect(this.view.$(SELECTORS.itemView)).toExist();
            });

            it('should appear if configurations were removed', function() {
                this.collection.add(this.model);
                expect(this.view.$(SELECTORS.itemView)).toExist();
                this.collection.remove(this.model);
                expect(this.view.$el).toContainText(emptyMessage);
                expect(this.view.$(SELECTORS.itemView)).not.toExist();
            });

            it('can create a new group configuration', function () {
                this.view.$('.new-button').click();
                expect($('.group-configuration-edit').length).toBeGreaterThan(0);
            });
        });
    });

    describe('Content groups list view', function() {
        var newGroupCss = '.new-button',
            addGroupCss = '.action-add',
            inputCss = '.collection-name-input',
            saveButtonCss = '.action-primary',
            cancelButtonCss = '.action-cancel',
            validationErrorCss = '.content-group-edit-error',
            scopedGroupSelector, createGroups, renderView, saveOrCancel, editNewGroup, editExistingGroup,
            verifyEditingGroup, respondToSave, expectGroupsVisible, correctValidationError;

        scopedGroupSelector = function(groupIndex, additionalSelectors) {
            var groupSelector = '.content-groups-list-item-' + groupIndex;
            if (additionalSelectors) {
                return groupSelector + ' ' + additionalSelectors;
            } else {
                return groupSelector;
            }
        };

        createGroups = function (groupNamesWithId) {
            var groups = new GroupCollection(_.map(groupNamesWithId, function (groupName, id) {
                    return {id: id, name: groupName};
                })),
                groupConfiguration = new GroupConfigurationModel({
                    id: 0,
                    name: 'Content Group Configuration',
                    groups: groups
                }, {canBeEmpty: true});
            groupConfiguration.urlRoot = '/mock_url';
            groupConfiguration.outlineUrl = '/mock_url';
            return groups;
        };

        renderView = function(groupNamesWithId) {
            var view = new GroupList({collection: createGroups(groupNamesWithId || {})}).render();
            appendSetFixtures(view.el);
            return view;
        };

        saveOrCancel = function(view, options, groupIndex) {
            if (options.save) {
                view.$(scopedGroupSelector(groupIndex, saveButtonCss)).click();
            } else if (options.cancel) {
                view.$(scopedGroupSelector(groupIndex, cancelButtonCss)).click();
            }
        };

        editNewGroup = function(view, options) {
            var newGroupIndex;
            if (view.collection.length === 0) {
                view.$(newGroupCss).click();
            } else {
                view.$(addGroupCss).click();
            }
            newGroupIndex = view.collection.length - 1;
            view.$(inputCss).val(options.newName);
            verifyEditingGroup(view, true, newGroupIndex);
            saveOrCancel(view, options, newGroupIndex);
        };

        editExistingGroup = function(view, options) {
            var groupIndex = options.groupIndex || 0;
            view.$(scopedGroupSelector(groupIndex, '.edit')).click();
            view.$(scopedGroupSelector(groupIndex, inputCss)).val(options.newName);
            saveOrCancel(view, options, groupIndex);
        };

        verifyEditingGroup = function(view, expectEditing, index) {
            // Should prevent the user from opening more than one edit
            // form at a time by removing the add button(s) when
            // editing a group.
            index = index || 0;
            if (expectEditing) {
                expect(view.$(scopedGroupSelector(index, '.content-group-edit'))).toExist();
                expect(view.$(newGroupCss)).not.toExist();
                expect(view.$(addGroupCss)).toHaveClass('is-hidden');
            } else {
                expect(view.$('.content-group-edit')).not.toExist();
                if (view.collection.length === 0) {
                    expect(view.$(newGroupCss)).toExist();
                    expect(view.$(addGroupCss)).not.toExist();
                } else {
                    expect(view.$(newGroupCss)).not.toExist();
                    expect(view.$(addGroupCss)).not.toHaveClass('is-hidden');
                }
            }
        };

        respondToSave = function(requests, view) {
            expect(requests.length).toBe(1);
            expect(requests[0].method).toBe('POST');
            expect(requests[0].url).toBe('/mock_url/0');
            AjaxHelpers.respondWithJson(requests, {
                name: 'Content Group Configuration',
                groups: view.collection.map(function(groupModel, index) {
                    return _.extend(groupModel.toJSON(), {id: index});
                })
            });
        };

        correctValidationError = function(view, requests, newGroupName) {
            expect(view.$(validationErrorCss)).toExist();
            verifyEditingGroup(view, true);
            view.$(inputCss).val(newGroupName);
            view.$(saveButtonCss).click();
            respondToSave(requests, view);
            expect(view.$(validationErrorCss)).not.toExist();
        };

        expectGroupsVisible = function(view, groupNames) {
            _.each(groupNames, function(groupName) {
                expect(view.$('.content-groups-list-item')).toContainText(groupName);
            });
        };

        beforeEach(function() {
            TemplateHelpers.installTemplates(
                ['content-group-editor', 'content-group-details', 'list']
            );
        });

        it('shows a message when no groups are present', function() {
            expect(renderView().$('.no-content'))
                .toContainText('You have not created any content groups yet.');
        });

        it('can render groups', function() {
            var groupNames = ['Group 1', 'Group 2', 'Group 3'];
            renderView(groupNames).$('.content-group-details').each(function(index) {
                expect($(this)).toContainText(groupNames[index]);
            });
        });

        it('can create an initial group and save', function() {
            var requests = AjaxHelpers.requests(this),
                newGroupName = 'New Group Name',
                view = renderView();
            editNewGroup(view, {newName: newGroupName, save: true});
            respondToSave(requests, view);
            verifyEditingGroup(view, false);
            expectGroupsVisible(view, [newGroupName]);
        });

        it('can add another group and save', function() {
            var requests = AjaxHelpers.requests(this),
                oldGroupName = 'Old Group Name',
                newGroupName = 'New Group Name',
                view = renderView({1: oldGroupName});
            editNewGroup(view, {newName: newGroupName, save: true});
            respondToSave(requests, view);
            verifyEditingGroup(view, false, 1);
            expectGroupsVisible(view, [oldGroupName, newGroupName]);
        });

        it('can cancel adding a group', function() {
            var requests = AjaxHelpers.requests(this),
                newGroupName = 'New Group Name',
                view = renderView();
            editNewGroup(view, {newName: newGroupName, cancel: true});
            expect(requests.length).toBe(0);
            verifyEditingGroup(view, false);
            expect(view.$()).not.toContainText(newGroupName);
        });

        it('can cancel editing a group', function() {
            var requests = AjaxHelpers.requests(this),
                originalGroupName = 'Original Group Name',
                view = renderView([originalGroupName]);
            editExistingGroup(view, {newName: 'New Group Name', cancel: true});
            verifyEditingGroup(view, false);
            expect(requests.length).toBe(0);
            expect(view.collection.at(0).get('name')).toBe(originalGroupName);
        });

        it('can show and correct a validation error', function() {
            var requests = AjaxHelpers.requests(this),
                newGroupName = 'New Group Name',
                view = renderView();
            editNewGroup(view, {newName: '', save: true});
            expect(requests.length).toBe(0);
            correctValidationError(view, requests, newGroupName);
        });

        it('can not invalidate an existing content group', function() {
            var requests = AjaxHelpers.requests(this),
                oldGroupName = 'Old Group Name',
                view = renderView([oldGroupName]);
            editExistingGroup(view, {newName: '', save: true});
            expect(requests.length).toBe(0);
            correctValidationError(view, requests, oldGroupName);
        });

        it('trims whitespace', function() {
            var requests = AjaxHelpers.requests(this),
                newGroupName = 'New Group Name',
                view = renderView();
            editNewGroup(view, {newName: '  ' + newGroupName + '  ', save: true});
            respondToSave(requests, view);
            expect(view.collection.at(0).get('name')).toBe(newGroupName);
        });

        it('only edits one form at a time', function() {
            var view = renderView();
            view.collection.add({name: 'Editing Group', editing: true});
            verifyEditingGroup(view, true);
        });

    });
});
