define([
    'jquery', 'underscore', 'js/common_helpers/template_helpers',
    'js/common_helpers/ajax_helpers', 'js/edxnotes/views/page_factory',
    'js/spec/edxnotes/custom_matchers'
], function($, _, TemplateHelpers, AjaxHelpers, NotesFactory, customMatchers) {
    'use strict';
    describe('EdxNotes NotesPage', function() {
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
        ];

        beforeEach(function() {
            customMatchers(this);
            loadFixtures('js/fixtures/edxnotes/edxnotes.html');
            TemplateHelpers.installTemplates([
                'templates/edxnotes/recent-activity-item',
                'templates/edxnotes/tab-item'
            ]);
            this.view = new NotesFactory({notesList: notes});
        });


        it('should be displayed properly', function() {
            var requests = AjaxHelpers.requests(this);

            expect(this.view.$('.tab-search-results')).not.toExist();
            expect(this.view.$('.tab-recent-activity')).toHaveClass('is-active');
            expect(this.view.$('.edx-notes-page-items-list')).toExist();

            this.view.$('.search-box input').val('test_query');
            this.view.$('.search-box button[type=submit]').click();
            AjaxHelpers.respondWithJson(requests, {
                total: 0,
                rows: []
            });
            expect(this.view.$('.tab-search-results')).toHaveClass('is-active');
            expect(this.view.$('.tab-recent-activity')).toExist();
        });

        it('should display update value and accompanying text', function() {
            _.each($('.edxnotes-page-item'), function(element, index) {
                expect($('dl > dt', element).last()).toContainText('Last Edited:');
                expect($('dl > dd', element).last()).toContainText(notes[index].updated);
            });
        });
    });
});
