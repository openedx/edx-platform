define([
    'jquery', 'underscore', 'js/views/pages/group_configurations',
    'js/models/group_configuration', 'js/collections/group_configuration',
    'common/js/spec_helpers/template_helpers'
], function($, _, GroupConfigurationsPage, GroupConfigurationModel, GroupConfigurationCollection, TemplateHelpers) {
    'use strict';
    describe('GroupConfigurationsPage', function() {
        var mockGroupConfigurationsPage = readFixtures(
                'mock/mock-group-configuration-page.underscore'
            ),
            groupConfigItemClassName = '.group-configurations-list-item';

        var initializePage = function(disableSpy) {
            var view = new GroupConfigurationsPage({
                el: $('#content'),
                experimentsEnabled: true,
                experimentGroupConfigurations: new GroupConfigurationCollection({
                    id: 0,
                    name: 'Configuration 1',
                    courseOutlineUrl: 'CourseOutlineUrl'
                }),
                contentGroupConfiguration: new GroupConfigurationModel({groups: []})
            });

            if (!disableSpy) {
                spyOn(view, 'addWindowActions');
            }

            return view;
        };

        var renderPage = function() {
            return initializePage().render();
        };

        beforeEach(function() {
            setFixtures(mockGroupConfigurationsPage);
            TemplateHelpers.installTemplates([
                'group-configuration-editor', 'group-configuration-details', 'content-group-details',
                'content-group-editor', 'group-edit', 'list'
            ]);

            jasmine.addMatchers({
                toBeExpanded: function() {
                    return {
                        compare: function(actual) {
                            return {
                                pass: Boolean($('a.group-toggle.hide-groups', $(actual)).length)
                            };
                        }
                    };
                }
            });
        });

        describe('Initial display', function() {
            // TODO fix this, see TNL-1475
            xit('can render itself', function() {
                var view = initializePage();
                expect(view.$('.ui-loading')).toBeVisible();
                view.render();
                expect(view.$(groupConfigItemClassName)).toExist();
                expect(view.$('.content-groups .no-content')).toExist();
                expect(view.$('.ui-loading')).toHaveClass('is-hidden');
            });
        });

        describe('Experiment group configurations', function() {
            beforeEach(function() {
                spyOn($.fn, 'focus');
                TemplateHelpers.installTemplate('group-configuration-details');
                this.view = initializePage(true);
            });

            it('should focus and expand if its id is part of url hash', function() {
                spyOn(this.view, 'getLocationHash').and.returnValue('#0');
                this.view.render();
                // We cannot use .toBeFocused due to flakiness.
                expect($.fn.focus).toHaveBeenCalled();
                expect(this.view.$(groupConfigItemClassName)).toBeExpanded();
            });

            it('should not focus on any experiment configuration if url hash is empty', function() {
                spyOn(this.view, 'getLocationHash').and.returnValue('');
                this.view.render();
                expect($.fn.focus).not.toHaveBeenCalled();
                expect(this.view.$(groupConfigItemClassName)).not.toBeExpanded();
            });

            it('should not focus on any experiment configuration if url hash contains wrong id', function() {
                spyOn(this.view, 'getLocationHash').and.returnValue('#1');
                this.view.render();
                expect($.fn.focus).not.toHaveBeenCalled();
                expect(this.view.$(groupConfigItemClassName)).not.toBeExpanded();
            });

            it('should not show a notification message if an experiment configuration is not changed', function() {
                this.view.render();
                expect(this.view.onBeforeUnload()).toBeUndefined();
            });

            it('should show a notification message if an experiment configuration is changed', function() {
                this.view.experimentGroupConfigurations.at(0).set('name', 'Configuration 2');
                expect(this.view.onBeforeUnload())
                    .toBe('You have unsaved changes. Do you really want to leave this page?');
            });
        });

        describe('Content groups', function() {
            beforeEach(function() {
                this.view = renderPage();
            });

            it('should not show a notification message if a content group is not changed', function() {
                expect(this.view.onBeforeUnload()).toBeUndefined();
            });

            it('should show a notification message if a content group is changed', function() {
                this.view.contentGroupConfiguration.get('groups').add({id: 0, name: 'Content Group'});
                expect(this.view.onBeforeUnload())
                    .toBe('You have unsaved changes. Do you really want to leave this page?');
            });
        });
    });
});
