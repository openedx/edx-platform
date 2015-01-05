define([
    'jquery', 'underscore', 'js/common_helpers/template_helpers',
    'js/spec/edxnotes/helpers', 'js/edxnotes/models/note',
    'js/edxnotes/views/note_item', 'js/spec/edxnotes/custom_matchers'
], function($, _, TemplateHelpers, Helpers, NoteModel, NoteItemView, customMatchers) {
    'use strict';
    describe('EdxNotes NoteItemView', function() {
        var getView = function (model) {
            model = new NoteModel(_.defaults(model || {}, {
                created: 'December 11, 2014 at 11:12AM',
                updated: 'December 11, 2014 at 11:12AM',
                text: 'Third added model',
                quote: Helpers.LONG_TEXT
            }));

            return new NoteItemView({model: model}).render();
        };

        beforeEach(function() {
            customMatchers(this);
            TemplateHelpers.installTemplate('templates/edxnotes/note-item');
        });

        it('can be rendered properly', function() {
            var view = getView();
            expect(view.$el).toContain('.note-excerpt-more-link');
            expect(view.$el).toContainText(Helpers.TRUNCATED_TEXT);
            expect(view.$el).toContainText('More');
            view.$('.note-excerpt-more-link').click();

            expect(view.$el).toContainText(Helpers.LONG_TEXT);
            expect(view.$el).toContainText('Less');

            view = getView({quote: Helpers.SHORT_TEXT});
            expect(view.$el).not.toContain('.note-excerpt-more-link');
            expect(view.$el).toContainText(Helpers.SHORT_TEXT);
        });

        it('should display update value and accompanying text', function() {
            var view = getView();
            expect(view.$('.reference-title').last()).toContainText('Last Edited:');
            expect(view.$('.reference-meta').last()).toContainText('December 11, 2014 at 11:12AM');
        });
    });
});
