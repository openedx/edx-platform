define([
    'jquery', 'underscore', 'js/common_helpers/template_helpers',
    'js/edxnotes/models/note', 'js/edxnotes/views/note_item',
    'js/spec/edxnotes/custom_matchers'
], function($, _, TemplateHelpers, NoteModel, NoteItemView, customMatchers) {
    'use strict';
    describe('EdxNotes NoteItemView', function() {
        var LONG_TEXT = 'Adipisicing elit, sed do eiusmod tempor incididunt ' +
                        'ut labore et dolore magna aliqua. Ut enim ad minim ' +
                        'veniam, quis nostrud exercitation ullamco laboris ' +
                        'nisi ut aliquip ex ea commodo consequat. Duis aute ' +
                        'irure dolor in reprehenderit in voluptate velit esse ' +
                        'cillum dolore eu fugiat nulla pariatur. Excepteur ' +
                        'sint occaecat cupidatat non proident, sunt in culpa ' +
                        'qui officia deserunt mollit anim id est laborum.',
            TRUNCATED_TEXT = 'Adipisicing elit, sed do eiusmod tempor incididunt ' +
                        'ut labore et dolore magna aliqua. Ut enim ad minim ' +
                        'veniam, quis nostrud exercitation ullamco laboris ' +
                        'nisi ut aliquip ex ea commodo consequat. Duis aute ' +
                        'irure dolor in reprehenderit in voluptate velit esse ' +
                        'cillum dolore eu fugiat nulla pariatur...',
            SHORT_TEXT = 'Adipisicing elit, sed do eiusmod tempor incididunt',
            getView;

        getView = function (model) {
            model = new NoteModel(_.defaults(model || {}, {
                created: 'December 11, 2014 at 11:12AM',
                updated: 'December 11, 2014 at 11:12AM',
                text: 'Third added model',
                quote: LONG_TEXT
            }));

            return new NoteItemView({model: model}).render();
        };

        beforeEach(function() {
            customMatchers(this);
            TemplateHelpers.installTemplates([
                'templates/edxnotes/note-item'
            ]);
        });

        it('can be rendered properly', function() {
            var view = getView();
            expect(view.$el).toContain('.note-excerpt-more-link');
            expect(view.$el).toContainText(TRUNCATED_TEXT);
            expect(view.$el).toContainText('More');
            view.$('.note-excerpt-more-link').click();

            expect(view.$el).toContainText(LONG_TEXT);
            expect(view.$el).toContainText('(Show less)');

            view = getView({quote: SHORT_TEXT});
            expect(view.$el).not.toContain('.note-excerpt-more-link');
            expect(view.$el).toContainText(SHORT_TEXT);
        });

        it('should display update value and accompanying text', function() {
            var view = getView();
            expect(view.$('.reference-title').last()).toContainText('Last Edited:');
            expect(view.$('.reference-meta').last()).toContainText('December 11, 2014 at 11:12AM');
        });
    });
});
