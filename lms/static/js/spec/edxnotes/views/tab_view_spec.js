define([
    'jquery',
    'backbone',
    'edx-ui-toolkit/js/utils/html-utils',
    'common/js/spec_helpers/template_helpers',
    'js/edxnotes/collections/tabs',
    'js/edxnotes/views/tabs_list',
    'js/edxnotes/views/tab_view'
], function ($, Backbone, HtmlUtils, TemplateHelpers, TabsCollection, TabsListView, TabView) {
    'use strict';
    describe('EdxNotes TabView', function() {
        var TestSubView = Backbone.View.extend({
                id: 'test-subview-panel',
                className: 'tab-panel',
                content: '<p>test view content</p>',
                render: function () {
                    this.$el.html(this.content);
                    return this;
                }
            }),
            TestView = TabView.extend({
                PanelConstructor: TestSubView,
                tabInfo: {
                    name: 'Test View Tab',
                    is_closable: true
                }
            }), getView;

        getView = function (tabsCollection, options) {
            var view;
            options = _.defaults(options || {}, {
                el: $('.wrapper-student-notes'),
                collection: [],
                tabsCollection: tabsCollection
            });
            view = new TestView(options);

            if (tabsCollection.length) {
                tabsCollection.at(0).activate();
            }

            return view;
        };

        beforeEach(function () {
            loadFixtures('js/fixtures/edxnotes/edxnotes.html');
            TemplateHelpers.installTemplates([
                'templates/edxnotes/note-item', 'templates/edxnotes/tab-item'
            ]);
            this.tabsCollection = new TabsCollection();
            this.tabsList = new TabsListView({collection: this.tabsCollection}).render();
            this.tabsList.$el.appendTo($('.tab-list'));
        });

        it('can create a tab and content on initialization', function () {
            var view = getView(this.tabsCollection);
            expect(this.tabsCollection).toHaveLength(1);
            expect(view.$('.tab')).toExist();
            expect(view.$('.wrapper-tabs')).toContainHtml('<p>test view content</p>');
        });

        it('cannot create a tab on initialization if flag is not set', function () {
            var view = getView(this.tabsCollection, {
                createTabOnInitialization: false
            });
            expect(this.tabsCollection).toHaveLength(0);
            expect(view.$('.tab')).not.toExist();
            expect(view.$('.wrapper-tabs')).not.toContainHtml('<p>test view content</p>');
        });

        it('can remove the content if tab becomes inactive', function () {
            var view = getView(this.tabsCollection);
            this.tabsCollection.add({identifier: 'second-tab'});
            view.$('#second-tab').click();
            expect(view.$('.tab')).toHaveLength(2);
            expect(view.$('.wrapper-tabs')).not.toContainHtml('<p>test view content</p>');
        });

        it('can remove the content if tab is closed', function () {
            var view = getView(this.tabsCollection);
            view.onClose =  jasmine.createSpy();
            view.$('.tab .action-close').click();
            expect(view.$('.tab')).toHaveLength(0);
            expect(view.$('.wrapper-tabs')).not.toContainHtml('<p>test view content</p>');
            expect(view.tabModel).toBeNull();
            expect(view.onClose).toHaveBeenCalled();
        });

        it('can correctly update the content of active tab', function () {
            var view = getView(this.tabsCollection);
            TestSubView.prototype.content = '<p>New content</p>';
            view.render();
            expect(view.$('.wrapper-tabs')).toContainHtml('<p>New content</p>');
            expect(view.$('.wrapper-tabs')).not.toContainHtml('<p>test view content</p>');
        });

        it('can show/hide error messages', function () {
            var view = getView(this.tabsCollection),
                errorHolder = view.$('.wrapper-msg');

            view.showErrorMessageHtml(HtmlUtils.HTML('<p>error message is here</p>'));
            expect(errorHolder).not.toHaveClass('is-hidden');
            expect(errorHolder.find('.copy')).toContainHtml('<p>error message is here</p>');

            view.hideErrorMessage();
            expect(errorHolder).toHaveClass('is-hidden');
            expect(errorHolder.find('.copy')).toBeEmpty();
        });

        it('should hide error messages before rendering', function () {
            var view = getView(this.tabsCollection),
                errorHolder = view.$('.wrapper-msg');
            view.showErrorMessageHtml('<p>error message is here</p>');
            view.render();
            expect(errorHolder).toHaveClass('is-hidden');
            expect(errorHolder.find('.copy')).toBeEmpty();
        });
    });
});
