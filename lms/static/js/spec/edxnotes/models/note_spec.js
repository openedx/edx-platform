define([
    'js/spec/edxnotes/helpers', 'js/edxnotes/collections/notes'
], function(Helpers, NotesCollection) {
    'use strict';
    describe('EdxNotes NoteModel', function() {
        beforeEach(function () {
            this.collection = new NotesCollection(
                {
                    'count': 2,
                    'current_page': 1,
                    'num_pages': 1,
                    'start': 0,
                    'next': null,
                    'previous': null,
                    'results': [
                        {quote: Helpers.LONG_TEXT, text: 'text\n with\r\nline\n\rbreaks \r'},
                        {quote: Helpers.SHORT_TEXT, text: 'text\n with\r\nline\n\rbreaks \r'}
                    ]
                },
                {
                    perPage: 10, parse: true
                }
            );
        });

        it('has correct values on initialization', function () {
            expect(this.collection.at(0).get('is_expanded')).toBeFalsy();
            expect(this.collection.at(0).get('show_link')).toBeTruthy();
            expect(this.collection.at(1).get('is_expanded')).toBeFalsy();
            expect(this.collection.at(1).get('show_link')).toBeFalsy();
        });

        it('can return appropriate `quote`', function () {
            var model = this.collection.at(0);

            // is_expanded = false, show_link = true
            expect(model.getQuote()).toBe(Helpers.PRUNED_TEXT);
            model.set('is_expanded', true);
            // is_expanded = true, show_link = true
            expect(model.getQuote()).toBe(Helpers.LONG_TEXT);
            model.set('show_link', false);
            model.set('is_expanded', false);
            // is_expanded = false, show_link = false
            expect(model.getQuote()).toBe(Helpers.LONG_TEXT);
        });

        it('can return appropriate `text`', function () {
            var model = this.collection.at(0);
            expect(model.get('text')).toBe('text\n with\r\nline\n\rbreaks \r');
        });
    });
});
