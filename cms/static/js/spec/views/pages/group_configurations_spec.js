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
            ), view;

        var initializePage = function (disableSpy) {
            view = new GroupConfigurationsPage({
                el: $('.content-primary'),
                collection: new GroupConfigurationCollection({
                    name: 'Configuration 1'
                })
            });

            if (!disableSpy) {
                spyOn(view, 'addGlobalActions');
            }
        };

        beforeEach(function () {
            setFixtures($('<script>', {
                id: 'no-group-configurations-tpl',
                type: 'text/template'
            }).text(noGroupConfigurationsTpl));
            appendSetFixtures(mockGroupConfigurationsPage);
        });

        describe('Initial display', function() {
            it('can render itself', function() {
                initializePage();
                expect(view.$('.ui-loading')).toBeVisible();
                view.render();
                expect(view.$('.no-group-configurations-content')).toBeTruthy();
                expect(view.$('.ui-loading')).toBeHidden();
            });
        });

        describe('on page close/change', function() {
            it('I see notification message if the model is changed',
            function() {
                var message;

                initializePage(true);
                view.render();
                message = view.onBeforeUnload();
                expect(message).toBeUndefined();
            });

            it('I do not see notification message if the model is not changed',
            function() {
                var expectedMessage = [
                    'You have unsaved changes. Do you really want to ',
                    'leave this page?'
                ].join(''), message;

                initializePage();
                view.render();
                view.collection.at(0).set('name', 'Configuration 2');
                message = view.onBeforeUnload();
                expect(message).toBe(expectedMessage);
            });
        });
    });
});
