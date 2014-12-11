define([
    'jquery', 'underscore', 'js/common_helpers/template_helpers', 'js/edxnotes/collections/notes',
    'js/edxnotes/collections/tabs', 'js/edxnotes/views/tabs/course_structure',
    'js/spec/edxnotes/custom_matchers', 'jasmine-jquery'
], function(
    $, _, TemplateHelpers, NotesCollection, TabsCollection, CourseStructureView, customMatchers
) {
    'use strict';
    describe('EdxNotes CourseStructureView', function() {
        var getChapter, getSection, getUnit, getView, getText, notes;

        getChapter = function (name, location, index, children) {
            return {
                display_name: name,
                location: 'i4x://chapter/' + location,
                index: index,
                children: _.map(children, function (i) {
                    return 'i4x://section/' + i;
                })
            };
        };

        getSection = function (name, location, children) {
            return {
                display_name: name,
                location: 'i4x://section/' + location,
                children: _.map(children, function (i) {
                    return 'i4x://unit/' + i;
                })
            };
        };

        getUnit = function (name, location) {
            return {
                display_name: name,
                location: 'i4x://unit/' + location,
                url: 'http://example.com'
            };
        };

        getText = function (selector) {
            return $(selector).map(function () {
                return _.trim($(this).text());
            }).toArray();
        };

        getView = function (collection, tabsCollection, options) {
            var view;

            options = _.defaults(options || {}, {
                el: $('.wrapper-student-notes'),
                collection: collection,
                tabsCollection: tabsCollection,
            });

            view = new CourseStructureView(options);
            tabsCollection.at(0).activate();

            return view;
        };

        notes = [
            {
                chapter: getChapter('Second Chapter', 0, 1, [1, 'w_n', 0]),
                section: getSection('Third Section', 0, ['w_n', 1, 0]),
                unit: getUnit('Fourth Unit', 0),
                created: 'December 11, 2014 at 11:12AM',
                updated: 'December 11, 2014 at 11:12AM',
                text: 'Third added model',
                quote: 'Note 4'
            },
            {
                chapter: getChapter('Second Chapter', 0, 1, [1, 'w_n', 0]),
                section: getSection('Third Section', 0, ['w_n', 1, 0]),
                unit: getUnit('Fourth Unit', 0),
                created: 'December 11, 2014 at 11:11AM',
                updated: 'December 11, 2014 at 11:11AM',
                text: 'Third added model',
                quote: 'Note 5'
            },
            {
                chapter: getChapter('Second Chapter', 0, 1, [1, 'w_n', 0]),
                section: getSection('Third Section', 0, ['w_n', 1, 0]),
                unit: getUnit('Third Unit', 1),
                created: 'December 11, 2014 at 11:11AM',
                updated: 'December 11, 2014 at 11:11AM',
                text: 'Second added model',
                quote: 'Note 3'
            },
            {
                chapter: getChapter('Second Chapter', 0, 1, [1, 'w_n', 0]),
                section: getSection('Second Section', 1, [3]),
                unit: getUnit('Second Unit', 3),
                created: 'December 11, 2014 at 11:10AM',
                updated: 'December 11, 2014 at 11:10AM',
                text: 'First added model',
                quote: 'Note 2'
            },
            {
                chapter: getChapter('First Chapter', 1, 0, [2]),
                section: getSection('First Section', 2, [4]),
                unit: getUnit('First Unit', 4),
                created: 'December 11, 2014 at 11:10AM',
                updated: 'December 11, 2014 at 11:10AM',
                text: 'First added model',
                quote: 'Note 1'
            }
        ];

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
            var view = getView(this.collection, this.tabsCollection),
                chapters = getText('.course-title'),
                sections = getText('.course-subtitle'),
                notes = getText('.note-excerpt-p');

            expect(this.tabsCollection).toHaveLength(1);
            expect(this.tabsCollection.at(0).attributes).toEqual({
                name: 'Course Structure',
                identifier: 'view-course-structure',
                icon: 'icon-list-ul',
                is_active: true,
                is_closable: false
            });
            expect(view.$('#structure-panel')).toExist();
            expect(chapters).toEqual(['First Chapter', 'Second Chapter', 'Second Chapter']);
            expect(sections).toEqual(['First Section', 'Second Section', 'Third Section']);
            expect(notes).toEqual(['Note 1', 'Note 2', 'Note 3', 'Note 4', 'Note 5']);
        });
    });
});
