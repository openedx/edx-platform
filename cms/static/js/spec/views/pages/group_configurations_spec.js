define([
    'jquery', 'underscore', 'js/views/pages/group_configurations',
    'js/collections/group_configuration', 'js/models/group_configuration', 'js/spec_helpers/edit_helpers'
], function ($, _, GroupConfigurationsPage, GroupConfigurationCollection, GroupConfigurationModel, view_helpers) {
    'use strict';
    describe('GroupConfigurationsPage', function() {
        var mockGroupConfigurationsPage = readFixtures(
                'mock/mock-group-configuration-page.underscore'
            ),
            itemClassName = '.group-configurations-list-item';

        var initializePage = function (disableSpy) {
            var view = new GroupConfigurationsPage({
                el: $('#content'),
                collection: new GroupConfigurationCollection({
                    id: 0,
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
            setFixtures(mockGroupConfigurationsPage);
            view_helpers.installTemplates([
                'no-group-configurations', 'group-configuration-edit',
                'group-configuration-details'
            ]);

            this.addMatchers({
                toBeExpanded: function () {
                    return Boolean($('a.group-toggle.hide-groups', $(this.actual)).length);
                }
            });
        });

        describe('Initial display', function() {
            it('can render itself', function() {
                var view = initializePage();
                expect(view.$('.ui-loading')).toBeVisible();
                view.render();
                expect(view.$(itemClassName)).toExist();
                expect(view.$('.ui-loading')).toHaveClass('is-hidden');
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
                var expectedMessage ='You have unsaved changes. Do you really want to leave this page?',
                    view = renderPage(),
                    message;

                view.collection.at(0).set('name', 'Configuration 2');
                message = view.onBeforeUnload();
                expect(message).toBe(expectedMessage);
            });
        });

        describe('Check that Group Configuration will focus and expand depending on content of url hash', function() {
            beforeEach(function () {
                spyOn($.fn, 'focus');
                view_helpers.installTemplate('group-configuration-details');
                this.view = initializePage(true);
            });

            it('should focus and expand group configuration if its id is part of url hash', function() {
                spyOn(this.view, 'getLocationHash').andReturn('#0');
                this.view.render();
                // We cannot use .toBeFocused due to flakiness.
                expect($.fn.focus).toHaveBeenCalled();
                expect(this.view.$(itemClassName)).toBeExpanded();
            });

            it('should not focus on any group configuration if url hash is empty', function() {
                spyOn(this.view, 'getLocationHash').andReturn('');
                this.view.render();
                expect($.fn.focus).not.toHaveBeenCalled();
                expect(this.view.$(itemClassName)).not.toBeExpanded();
            });

            it('should not focus on any group configuration if url hash contains wrong id', function() {
                spyOn(this.view, 'getLocationHash').andReturn('#1');
                this.view.render();
                expect($.fn.focus).not.toHaveBeenCalled();
                expect(this.view.$(itemClassName)).not.toBeExpanded();
            });
        });

        it('create new group configuration', function () {
            var view = renderPage();

            clickNewConfiguration(view);
            expect($('.group-configuration-edit').length).toBeGreaterThan(0);
        });
    });
});
