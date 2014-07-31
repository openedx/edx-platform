define([
    'jquery', 'underscore', 'js/views/pages/group_configurations',
    'js/collections/group_configuration'
], function ($, _, GroupConfigurationsPage, GroupConfigurationCollection) {
    'use strict';
    describe('GroupConfigurationsPage', function() {
        var mockGroupConfigurationsPage = readFixtures(
                'mock/mock-group-configuration-page.underscore'
            ),
            noGroupConfigurationsTpl = readFixtures(
                'no-group-configurations.underscore'
            ),
            groupConfigurationEditTpl = readFixtures(
                'group-configuration-edit.underscore'
            );

        var initializePage = function (disableSpy) {
            var view = new GroupConfigurationsPage({
                el: $('#content'),
                collection: new GroupConfigurationCollection({
                    name: 'Configuration 1'
                })
            });

            if (!disableSpy) {
                spyOn(view, 'addWindowActions');
            }

            return view;
        };

        var renderPage = function () {
            return initializePage().render();
        };

        var  clickNewConfiguration = function (view) {
            view.$('.nav-actions .new-button').click();
        };

        beforeEach(function () {
            setFixtures($('<script>', {
                id: 'no-group-configurations-tpl',
                type: 'text/template'
            }).text(noGroupConfigurationsTpl));

            appendSetFixtures($('<script>', {
                id: 'group-configuration-edit-tpl',
                type: 'text/template'
            }).text(groupConfigurationEditTpl));

            appendSetFixtures(mockGroupConfigurationsPage);
        });

        describe('Initial display', function() {
            it('can render itself', function() {
                var view = initializePage();
                expect(view.$('.ui-loading')).toBeVisible();
                view.render();
                expect(view.$('.no-group-configurations-content')).toBeTruthy();
                expect(view.$('.ui-loading')).toBeHidden();
            });
        });

        describe('on page close/change', function() {
            it('I see notification message if the model is changed',
            function() {
                var view = initializePage(true),
                    message;

                view.render();
                message = view.onBeforeUnload();
                expect(message).toBeUndefined();
            });

            it('I do not see notification message if the model is not changed',
            function() {
                var expectedMessage = [
                        'You have unsaved changes. Do you really want to ',
                        'leave this page?'
                    ].join(''),
                        view = renderPage(),
                        message;

                view.collection.at(0).set('name', 'Configuration 2');
                message = view.onBeforeUnload();
                expect(message).toBe(expectedMessage);
            });
        });

        it('create new group configuration', function () {
            var view = renderPage();

            clickNewConfiguration(view);
            expect($('.group-configuration-edit').length).toBeGreaterThan(0);
        });
    });
});
