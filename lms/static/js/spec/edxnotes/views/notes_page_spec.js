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
                'templates/edxnotes/note-item',
                'templates/edxnotes/tab-item'
            ]);
            this.view = new NotesFactory({notesList: notes});
        });


        it('should be displayed properly', function() {
            var requests = AjaxHelpers.requests(this);

            expect(this.view.$('#view-search-results')).not.toExist();
            expect(this.view.$('#view-recent-activity')).toHaveClass('is-active');
            expect(this.view.$('.tab-panel')).toExist();

            this.view.$('.search-notes-input').val('test_query');
            this.view.$('.search-notes-submit').click();
            AjaxHelpers.respondWithJson(requests, {
                total: 0,
                rows: []
            });
            expect(this.view.$('#view-search-results')).toHaveClass('is-active');
            expect(this.view.$('#view-recent-activity')).toExist();
        });
    });
});
