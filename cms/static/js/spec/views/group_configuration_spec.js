define([
    'js/models/course', 'js/models/group_configuration',
    'js/collections/group_configuration',
    'js/views/group_configuration_details',
    'js/views/group_configurations_list', 'js/views/group_configuration_edit',
    'js/views/group_configuration_item', 'js/views/feedback_notification',
    'js/spec_helpers/create_sinon', 'js/spec_helpers/edit_helpers',
    'jasmine-stealth'
], function(
    Course, GroupConfigurationModel, GroupConfigurationCollection,
    GroupConfigurationDetails, GroupConfigurationsList, GroupConfigurationEdit,
    GroupConfigurationItem, Notification, create_sinon, view_helpers
) {
    'use strict';
    var SELECTORS = {
        detailsView: '.group-configuration-details',
        editView: '.group-configuration-edit',
        itemView: '.group-configurations-list-item',
        group: '.group',
        name: '.group-configuration-name',
        description: '.group-configuration-description',
        groupsCount: '.group-configuration-groups-count',
        groupsAllocation: '.group-allocation',
        errorMessage: '.group-configuration-edit-error',
        inputName: '.group-configuration-name-input',
        inputDescription: '.group-configuration-description-input'
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
            }
        });
    });

    afterEach(function() {
        delete window.course;
    });

    describe('GroupConfigurationDetails', function() {
        beforeEach(function() {
            view_helpers.installTemplate('group-configuration-details', true);

            this.model = new GroupConfigurationModel({
                name: 'Configuration',
                description: 'Configuration Description',
                id: 0
            });

            this.collection = new GroupConfigurationCollection([ this.model ]);
            this.view = new GroupConfigurationDetails({
                model: this.model
            });
            appendSetFixtures(this.view.render().el);
        });

        it('should render properly', function() {
            expect(this.view.$el).toContainText('Configuration');
            expect(this.view.$el).toContainText('ID: 0');
        });

        it('should show groups appropriately', function() {
            this.model.get('groups').add([{}, {}, {}]);
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
            this.model.get('groups').add([{}, {}, {}]);
            this.model.set('showGroups', true);
            this.view.$('.hide-groups').click();

            expect(this.model.get('showGroups')).toBeFalsy();
            expect(this.view.$(SELECTORS.group)).not.toExist();
            expect(this.view.$(SELECTORS.groupsCount))
                .toContainText('Contains 3 groups');
            expect(this.view.$(SELECTORS.description)).not.toExist();
            expect(this.view.$(SELECTORS.groupsAllocation)).not.toExist();
        });
    });

    describe('GroupConfigurationEdit', function() {

        var setValuesToInputs = function (view, values) {
            _.each(values, function (value, selector) {
                if (SELECTORS[selector]) {
                    view.$(SELECTORS[selector]).val(value);
                }
            });
        };

        beforeEach(function() {
            view_helpers.installViewTemplates();
            view_helpers.installTemplate('group-configuration-edit');

            this.model = new GroupConfigurationModel({
                name: 'Configuration',
                description: 'Configuration Description',
                id: 0,
                editing: true
            });
            this.collection = new GroupConfigurationCollection([this.model]);
            this.collection.url = '/group_configurations';
            this.view = new GroupConfigurationEdit({
                model: this.model
            });
            appendSetFixtures(this.view.render().el);
        });

        it('should render properly', function() {
            expect(this.view).toBeCorrectValuesInInputs({
                name: 'Configuration',
                description: 'Configuration Description'
            });
        });

        it('should save properly', function() {
            var requests = create_sinon.requests(this),
                notificationSpy = view_helpers.createNotificationSpy();

            setValuesToInputs(this.view, {
                inputName: 'New Configuration',
                inputDescription: 'New Description'
            });

            this.view.$('form').submit();
            view_helpers.verifyNotificationShowing(notificationSpy, /Saving/);
            requests[0].respond(200);
            view_helpers.verifyNotificationHidden(notificationSpy);

            expect(this.model).toBeCorrectValuesInModel({
                name: 'New Configuration',
                description: 'New Description'
            });
            expect(this.view.$el).not.toExist();
        });

        it('does not hide saving message if failure', function() {
            var requests = create_sinon.requests(this),
                notificationSpy = view_helpers.createNotificationSpy();

            setValuesToInputs(this.view, { inputName: 'New Configuration' });
            this.view.$('form').submit();
            view_helpers.verifyNotificationShowing(notificationSpy, /Saving/);
            create_sinon.respondWithError(requests);
            view_helpers.verifyNotificationShowing(notificationSpy, /Saving/);
        });

        it('does not save on cancel', function() {
            setValuesToInputs(this.view, {
                inputName: 'New Configuration',
                inputDescription: 'New Description'
            });
            this.view.$('.action-cancel').click();
            expect(this.model).toBeCorrectValuesInModel({
                name: 'Configuration',
                description: 'Configuration Description'
            });
            // Model is still exist in the collection
            expect(this.collection.indexOf(this.model)).toBeGreaterThan(-1);
            expect(this.collection.length).toBe(1);
        });

        it('should be removed on cancel if it is a new item', function() {
            spyOn(this.model, 'isNew').andReturn(true);
            setValuesToInputs(this.view, {
                inputName: 'New Configuration',
                inputDescription: 'New Description'
            });
            this.view.$('.action-cancel').click();
            // Model is removed from the collection
            expect(this.collection.length).toBe(0);
        });

        it('should be possible to correct validation errors', function() {
            var requests = create_sinon.requests(this);

            // Set incorrect value
            setValuesToInputs(this.view, { inputName: '' });
            // Try to save
            this.view.$('form').submit();
            // See error message
            expect(this.view.$(SELECTORS.errorMessage)).toContainText(
                'Group Configuration name is required'
            );
            // No request
            expect(requests.length).toBe(0);
            // Set correct value
            setValuesToInputs(this.view, { inputName: 'New Configuration' });
            // Try to save
            this.view.$('form').submit();
            requests[0].respond(200);
            // Model is updated
            expect(this.model).toBeCorrectValuesInModel({
                name: 'New Configuration'
            });
            // Error message disappear
            expect(this.view.$(SELECTORS.errorMessage)).not.toExist();
            expect(requests.length).toBe(1);
        });
    });

    describe('GroupConfigurationsList', function() {
        beforeEach(function() {
            view_helpers.installTemplate('no-group-configurations', true);

            this.collection = new GroupConfigurationCollection();
            this.view = new GroupConfigurationsList({
                collection: this.collection
            });
            appendSetFixtures(this.view.render().el);
        });

        describe('empty template', function () {
            it('should be rendered if no group configurations', function() {
                expect(this.view.$el).toContainText(
                    'You haven\'t created any group configurations yet.'
                );
                expect(this.view.$el).toContain('.new-button');
                expect(this.view.$(SELECTORS.itemView)).not.toExist();
            });

            it('should disappear if group configuration is added', function() {
                var emptyMessage = 'You haven\'t created any group ' +
                    'configurations yet.';

                expect(this.view.$el).toContainText(emptyMessage);
                expect(this.view.$(SELECTORS.itemView)).not.toExist();
                this.collection.add([{}]);
                expect(this.view.$el).not.toContainText(emptyMessage);
                expect(this.view.$(SELECTORS.itemView)).toExist();
            });
        });
    });

    describe('GroupConfigurationItem', function() {
        beforeEach(function() {
            view_helpers.installTemplate('group-configuration-edit', true);
            view_helpers.installTemplate('group-configuration-details');
            this.model = new GroupConfigurationModel({ id: 0 });
            this.collection = new GroupConfigurationCollection([ this.model ]);
            this.view = new GroupConfigurationItem({
                model: this.model
            });
            appendSetFixtures(this.view.render().el);
        });

        it('should render properly', function() {
            // Details view by default
            expect(this.view.$(SELECTORS.detailsView)).toExist();
            this.view.$('.action-edit .edit').click();
            expect(this.view.$(SELECTORS.editView)).toExist();
            expect(this.view.$(SELECTORS.detailsView)).not.toExist();
            this.view.$('.action-cancel').click();
            expect(this.view.$(SELECTORS.detailsView)).toExist();
            expect(this.view.$(SELECTORS.editView)).not.toExist();
        });
    });
});


