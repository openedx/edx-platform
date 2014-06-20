define([
    'js/models/group_configuration', 'js/models/course',
    'js/collections/group_configuration', 'js/views/group_configuration_details',
    'js/views/group_configurations_list', 'jasmine-stealth'
], function(
    GroupConfigurationModel, Course, GroupConfigurationSet,
    GroupConfigurationDetails, GroupConfigurationsList
) {
    'use strict';
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
            }
        });
    });

    afterEach(function() {
        delete window.course;
    });

    describe('GroupConfigurationDetails', function() {
        var tpl = readFixtures('group-configuration-details.underscore');

        beforeEach(function() {
            setFixtures($('<script>', {
                id: 'group-configuration-details-tpl',
                type: 'text/template'
            }).text(tpl));

            this.model = new GroupConfigurationModel({
                name: 'Configuration',
                description: 'Configuration Description',
                id: 0
            });

            spyOn(this.model, 'destroy').andCallThrough();
            this.collection = new GroupConfigurationSet([ this.model ]);
            this.view = new GroupConfigurationDetails({
                model: this.model
            });
        });

        describe('Basic', function() {
            it('should render properly', function() {
                this.view.render();

                expect(this.view.$el).toContainText('Configuration');
                expect(this.view.$el).toContainText('ID: 0');
            });

            it('should show groups appropriately', function() {
                this.model.get('groups').add([{}, {}, {}]);
                this.model.set('showGroups', false);
                this.view.render().$('.show-groups').click();

                expect(this.model.get('showGroups')).toBeTruthy();
                expect(this.view.$el.find('.group').length).toBe(5);
                expect(this.view.$el.find('.group-configuration-groups-count'))
                    .not.toExist();
                expect(this.view.$el.find('.group-configuration-description'))
                    .toContainText('Configuration Description');
                expect(this.view.$el.find('.group-allocation'))
                    .toContainText('20%');
            });

            it('should hide groups appropriately', function() {
                this.model.get('groups').add([{}, {}, {}]);
                this.model.set('showGroups', true);
                this.view.render().$('.hide-groups').click();

                expect(this.model.get('showGroups')).toBeFalsy();
                expect(this.view.$el.find('.group').length).toBe(0);
                expect(this.view.$el.find('.group-configuration-groups-count'))
                    .toContainText('Contains 5 groups');
                expect(this.view.$el.find('.group-configuration-description'))
                    .not.toExist();
                expect(this.view.$el.find('.group-allocation'))
                    .not.toExist();
            });
        });
    });

    describe('GroupConfigurationsList', function() {
        var noGroupConfigurationsTpl = readFixtures(
            'no-group-configurations.underscore'
        );

        beforeEach(function() {
            var showEl = $('<li>');

            setFixtures($('<script>', {
                id: 'no-group-configurations-tpl',
                type: 'text/template'
            }).text(noGroupConfigurationsTpl));

            this.showSpies = spyOnConstructor(
                window, 'GroupConfigurationDetails', [ 'render' ]
            );
            this.showSpies.render.andReturn(this.showSpies);
            this.showSpies.$el = showEl;
            this.showSpies.el = showEl.get(0);
            this.collection = new GroupConfigurationSet();
            this.view = new GroupConfigurationsList({
                collection: this.collection
            });
            this.view.render();
        });

        var message = 'should render the empty template if there are no group ' +
                      'configurations';
        it(message, function() {
            expect(this.view.$el).toContainText(
                'You haven\'t created any group configurations yet.'
            );
            expect(this.view.$el).not.toContain('.new-button');
            expect(this.showSpies.constructor).not.toHaveBeenCalled();
        });

        it('should render GroupConfigurationDetails views by default', function() {
            this.collection.add([{}, {}, {}]);
            this.view.render();

            expect(this.view.$el).not.toContainText(
                'You haven\'t created any group configurations yet.'
            );
            expect(this.view.$el.find('.group-configuration').length).toBe(3);
        });
    });
});
