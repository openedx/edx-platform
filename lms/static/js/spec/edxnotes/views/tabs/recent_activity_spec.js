define([
    'jquery', 'common/js/spec_helpers/template_helpers', 'js/edxnotes/collections/notes',
    'js/edxnotes/collections/tabs', 'js/edxnotes/views/tabs/recent_activity',
    'js/spec/edxnotes/custom_matchers', 'jasmine-jquery'
], function(
    $, TemplateHelpers, NotesCollection, TabsCollection, RecentActivityView, customMatchers
) {
    'use strict';
    describe('EdxNotes RecentActivityView', function() {
        var notes = [
            {
                created: 'December 11, 2014 at 11:12AM',
                updated: 'December 11, 2014 at 11:12AM',
                text: 'Third added model',
                quote: 'Should be listed first'
            },
            {
                created: 'December 11, 2014 at 11:11AM',
                updated: 'December 11, 2014 at 11:11AM',
                text: 'Second added model',
                quote: 'Should be listed second'
            },
            {
                created: 'December 11, 2014 at 11:10AM',
                updated: 'December 11, 2014 at 11:10AM',
                text: 'First added model',
                quote: 'Should be listed third'
            }
        ], getView;

        getView = function (collection, tabsCollection, options) {
            var view;

            options = _.defaults(options || {}, {
                el: $('.wrapper-student-notes'),
                collection: collection,
                tabsCollection: tabsCollection,
            });

            view = new RecentActivityView(options);
            tabsCollection.at(0).activate();

            return view;
        };

        beforeEach(function () {
            customMatchers(this);
            loadFixtures('js/fixtures/edxnotes/edxnotes.html');
            TemplateHelpers.installTemplates([
                'templates/edxnotes/note-item', 'templates/edxnotes/tab-item'
            ]);

            this.collection = new NotesCollection(notes);
            this.tabsCollection = new TabsCollection();
        });

        it('displays a tab and content with proper data and order', function () {
            var view = getView(this.collection, this.tabsCollection);

            expect(this.tabsCollection).toHaveLength(1);
            expect(this.tabsCollection.at(0).toJSON()).toEqual({
                name: 'Recent Activity',
                identifier: 'view-recent-activity',
                icon: 'fa fa-clock-o',
                is_active: true,
                is_closable: false,
                view: 'Recent Activity'
            });
            expect(view.$('#recent-panel')).toExist();
            expect(view.$('.note')).toHaveLength(3);
            _.each(view.$('.note'), function(element, index) {
                expect($('.note-comments', element)).toContainText(notes[index].text);
                expect($('.note-excerpt', element)).toContainText(notes[index].quote);
            });
        });
    });
});
