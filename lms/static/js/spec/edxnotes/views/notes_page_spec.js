define([
    'jquery', 'underscore', 'js/common_helpers/template_helpers', 'js/edxnotes/views/page_factory'
], function($, _, TemplateHelpers, NotesFactory) {
    'use strict';
    describe('NotesPage', function() {
        var notes = [
            {
                created: 'December 11, 2014 at 11:12AM',
                updated: 'December 11, 2014 at 11:12AM',
                text: 'First added model',
                quote: 'Should be listed third'
            },
            {
                created: 'December 11, 2014 at 11:11AM',
                updated: 'December 11, 2014 at 11:11AM',
                text: 'Third added model',
                quote: 'Should be listed second'
            },
            {
                created: 'December 11, 2014 at 11:10AM',
                updated: 'December 11, 2014 at 11:10AM',
                text: 'Second added model',
                quote: 'Should be listed first'
            }
        ];

        beforeEach(function() {
            setFixtures('<div class="edx-notes-page-wrapper"><div class="course-info"></div></div>');
            TemplateHelpers.installTemplate('templates/edxnotes/note-item');
            this.view = new NotesFactory({notesList: notes});
        });

        describe('Initial rendering', function() {
            it('should not show the loading indicator', function() {
                expect('.ui-loading').not.toBeVisible();
            });

            it('should have certain elements', function() {
                expect($('div.edx-notes-page-wrapper')).toExist();
                expect($('div.course-info')).toExist();
                expect($('div.edx-notes-page-items-list')).toExist();
            });

            it('should be displayed properly', function() {
                var pageItems = $('article.edx-notes-page-item');
                // Make sure we have exactly 3 page items created
                expect(pageItems.length).toEqual(3);
                // Check that the ordering is correct and each model's text and quote are rendered
                _.each(pageItems, function(el, index) {
                    expect(pageItems.eq(index).find('.edx-notes-item-text').text()).toContain(notes[index].text);
                    expect(pageItems.eq(index).find('.edx-notes-item-quote').text()).toContain(notes[index].quote);
                });
            });

            it('should display update value and accompanying text', function() {
                var pageItems = $('article.edxnotes-page-item');

                _.each(pageItems, function(el, index) {
                    expect(pageItems.eq(index).find('dl>dt').last().text()).toBe('Last Edited:');
                    expect(pageItems.eq(index).find('dl>dd').last().text()).toBe(notes[index].updated);
                });
            });
        });
    });
});
