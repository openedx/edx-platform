define([
    'jquery', 'underscore', 'common/js/spec_helpers/template_helpers',
    'common/js/spec_helpers/ajax_helpers', 'js/spec/edxnotes/helpers',
    'js/edxnotes/views/page_factory', 'js/spec/edxnotes/custom_matchers'
], function($, _, TemplateHelpers, AjaxHelpers, Helpers, NotesFactory, customMatchers) {
    'use strict';
    describe('EdxNotes NotesPage', function() {
        var notes = Helpers.getDefaultNotes();

        beforeEach(function() {
            customMatchers(this);
            loadFixtures('js/fixtures/edxnotes/edxnotes.html');
            TemplateHelpers.installTemplates([
                'templates/edxnotes/note-item', 'templates/edxnotes/tab-item'
            ]);
            this.view = new NotesFactory({notesList: notes});
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
                total: 0,
                rows: []
            });
            expect(this.view.$('#view-search-results')).toHaveClass('is-active');
            expect(this.view.$('#view-recent-activity')).toExist();
            expect(this.view.$('#view-course-structure')).toExist();
        });
    });
});
