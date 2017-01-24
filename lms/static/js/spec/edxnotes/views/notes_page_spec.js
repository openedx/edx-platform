define([
    'jquery', 'underscore', 'common/js/spec_helpers/template_helpers',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers', 'js/spec/edxnotes/helpers',
    'js/edxnotes/views/page_factory'
], function($, _, TemplateHelpers, AjaxHelpers, Helpers, NotesFactory) {
    'use strict';
    describe('EdxNotes NotesPage', function() {
        var notes = Helpers.getDefaultNotes();

        beforeEach(function() {
            loadFixtures('js/fixtures/edxnotes/edxnotes.html');
            TemplateHelpers.installTemplates([
                'templates/edxnotes/note-item', 'templates/edxnotes/tab-item'
            ]);
            this.view = new NotesFactory({notes: notes, pageSize: 10});
        });

        it('should be displayed properly', function() {
            var requests = AjaxHelpers.requests(this),
                tab;

            expect(this.view.$('#view-search-results')).not.toExist();
            tab = this.view.$('#view-recent-activity');
            expect(tab).toHaveClass('is-active');
            expect(tab.index()).toBe(0);

            tab = this.view.$('#view-course-structure');
            expect(tab).toExist();
            expect(tab.index()).toBe(1);

            expect(this.view.$('.tab-panel')).toExist();

            this.view.$('.search-notes-input').val('test_query');
            this.view.$('.search-notes-submit').click();
            AjaxHelpers.respondWithJson(requests, {
                'count': 0,
                'current_page': 1,
                'num_pages': 1,
                'start': 0,
                'next': null,
                'previous': null,
                'results': []
            });
            expect(this.view.$('#view-search-results')).toHaveClass('is-active');
            expect(this.view.$('#view-recent-activity')).toExist();
            expect(this.view.$('#view-course-structure')).toExist();
        });
    });
});
