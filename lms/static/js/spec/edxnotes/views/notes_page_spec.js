define(['jquery', 'underscore', 'js/common_helpers/template_helpers', 'js/edxnotes/views/page_factory'],
    function($, _, TemplateHelpers, NotesFactory) {
        'use strict';

        describe('NotesPage', function() {
            var view,
                // Format: December 11, 2014 at 11:10AM
                displayTime = [
                    'December 11, 2014 at 11:10AM',
                    'December 11, 2014 at 11:11AM',
                    'December 11, 2014 at 11:12AM'
                ],
                notes = [
                    {
                        created: '2014-10-10T10:10:10.012+00:00',
                        updated: '2014-10-10T10:10:10.012+00:00',
                        text: 'First added model',
                        quote: 'Should be listed third'
                    },
                    {
                        created: '2014-10-10T10:10:10.010+00:00',
                        updated: '2014-10-10T10:10:10.010+00:00',
                        text: 'Second added model',
                        quote: 'Should be listed first'
                    },
                    {
                        created: '2014-10-10T10:10:10.011+00:00',
                        updated: '2014-10-10T10:10:10.011+00:00',
                        text: 'Third added model',
                        quote: 'Should be listed second'
                    }
                ];

            beforeEach(function() {
                setFixtures('<div class="edx-notes-page-wrapper"><div class="course-info"></div></div>');
                TemplateHelpers.installTemplate('templates/edxnotes/note-item');

                view = new NotesFactory({notesList: notes});
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

                it('should order notes by ascending date of their last update', function() {
                    var pageItems = $('article.edx-notes-page-item'),
                        sortedNotes = _.sortBy(notes, function(note){return note.updated;});
                    // Make sure we have exactly 3 page items created
                    expect(pageItems.length).toEqual(3);
                    // Check that the ordering is correct and each model's text and quote are rendered
                    _.each(pageItems, function(el, index) {
                        expect(pageItems.eq(index).find('.edx-notes-item-text').text()).toContain(sortedNotes[index].text);
                        expect(pageItems.eq(index).find('.edx-notes-item-quote').text()).toContain(sortedNotes[index].quote);
                    });
                });

                it('should display update value and accompanying text', function() {
                    var pageItems = $('article.edxnotes-page-item');

                    _.each(pageItems, function(el, index) {
                        expect(pageItems.eq(index).find('dl>dt').last().text()).toBe('Last Edited:');
                        expect(pageItems.eq(index).find('dl>dd').last().text()).toBe(displayTime[index]);
                    });
                });
            });
        });
    }
);
