define(['js/edxnotes/collections/notes'], function(NotesCollection) {
    'use strict';
    describe('EdxNotes NoteModel', function() {
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
           SHORT_TEXT = 'Adipisicing elit, sed do eiusmod tempor incididunt';

        beforeEach(function () {
            this.collection = new NotesCollection([
                {quote: LONG_TEXT},
                {quote: SHORT_TEXT}
            ]);
        });

        it('has correct values on initialization', function () {
            expect(this.collection.at(0).get('is_expanded')).toBeFalsy();
            expect(this.collection.at(0).get('show_link')).toBeTruthy();
            expect(this.collection.at(1).get('is_expanded')).toBeFalsy();
            expect(this.collection.at(1).get('show_link')).toBeFalsy();
        });

        it('can return appropriate note text', function () {
            var model = this.collection.at(0);

            // is_expanded = false, show_link = true
            expect(model.getNoteText()).toBe(TRUNCATED_TEXT);
            model.set('is_expanded', true);
            // is_expanded = true, show_link = true
            expect(model.getNoteText()).toBe(LONG_TEXT);
            model.set('show_link', false);
            model.set('is_expanded', false);
            // is_expanded = false, show_link = false
            expect(model.getNoteText()).toBe(LONG_TEXT);
        });
    });
});
