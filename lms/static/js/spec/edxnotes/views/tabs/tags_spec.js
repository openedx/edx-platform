define([
    'jquery', 'underscore', 'common/js/spec_helpers/template_helpers', 'js/spec/edxnotes/helpers',
    'js/edxnotes/collections/notes', 'js/edxnotes/collections/tabs',
    'js/edxnotes/views/tabs/tags'
], function(
    $, _, TemplateHelpers, Helpers, NotesCollection, TabsCollection, TagsView
) {
    'use strict';
    describe('EdxNotes TagsView', function() {
        var notes = Helpers.getDefaultNotes(),
            getView, getText, getNoteText;

        getText = function (selector) {
            return $(selector).map(function () { return _.trim($(this).text()); }).toArray();
        };

        getNoteText = function (groupIndex) {
            return $($('.note-group')[groupIndex]).find('.note-excerpt-p').map(function () {
                return _.trim($(this).text());
            }).toArray();
        };

        getView = function (collection, tabsCollection, options) {
            var view;

            options = _.defaults(options || {}, {
                el: $('.wrapper-student-notes'),
                collection: collection,
                tabsCollection: tabsCollection
            });

            view = new TagsView(options);
            tabsCollection.at(0).activate();

            return view;
        };

        beforeEach(function () {
            loadFixtures('js/fixtures/edxnotes/edxnotes.html');
            TemplateHelpers.installTemplates([
                'templates/edxnotes/note-item', 'templates/edxnotes/tab-item'
            ]);

            this.collection = new NotesCollection(notes, {perPage: 10, parse: true});
            this.tabsCollection = new TabsCollection();
        });

        it('displays a tab and content properly ordered by tag', function () {
            var view = getView(this.collection, this.tabsCollection),
                tags = getText('.tags-title'),
                pumpkinNotes = getNoteText(0),
                pieNotes = getNoteText(1),
                yummyNotes = getNoteText(2),
                noTagsNotes = getNoteText(3);

            expect(this.tabsCollection).toHaveLength(1);
            expect(this.tabsCollection.at(0).toJSON()).toEqual({
                name: 'Tags',
                identifier: 'view-tags',
                icon: 'fa fa-tag',
                is_active: true,
                is_closable: false,
                view: 'Tags'
            });
            expect(view.$('#tags-panel')).toExist();

            // Pumpkin notes has the greatest number of notes, and therefore should come first.
            // Yummy and pie notes have the same number of notes. They should be sorted alphabetically.
            // "no tags" should always be last.
            expect(tags).toEqual(['pumpkin (3)', 'pie (2)', 'yummy (2)', '[no tags] (1)']);

            expect(pumpkinNotes).toEqual(['Note 4', 'Note 2', 'Note 1']);
            expect(yummyNotes).toEqual(['Note 4', 'Note 3']);
            expect(pieNotes).toEqual(['Note 2', 'Note 1']);
            expect(noTagsNotes).toEqual(['Note 5']);
        });
    });
});
