define([
    'js/spec/edxnotes/helpers', 'js/edxnotes/collections/notes'
], function(Helpers, NotesCollection) {
    'use strict';
    describe('EdxNotes NotesCollection', function() {
        var notes = Helpers.getDefaultNotes();

        beforeEach(function() {
            this.collection = new NotesCollection(notes, {perPage: 10, parse: true});
        });

        it('can return correct course structure', function() {
            var structure = this.collection.getCourseStructure();

            expect(structure.chapters).toEqual([
                Helpers.getChapter('First Chapter', 1, 0, [2]),
                Helpers.getChapter('Second Chapter', 0, 1, [1, 'w_n', 0])
            ]);

            expect(structure.sections).toEqual({
                'i4x://section/0': Helpers.getSection('Third Section', 0, ['w_n', 1, 0]),
                'i4x://section/1': Helpers.getSection('Second Section', 1, [2]),
                'i4x://section/2': Helpers.getSection('First Section', 2, [3])
            });

            var compareUnits = function(structureUnits, collectionUnits) {
                expect(structureUnits.length === collectionUnits.length).toBeTruthy();
                for (var i = 0; i < structureUnits.length; i++) {
                    expect(structureUnits[i].attributes).toEqual(collectionUnits[i].attributes);
                }
            };

            var units = {
                'i4x://unit/0': [this.collection.at(0), this.collection.at(1)],
                'i4x://unit/1': [this.collection.at(2)],
                'i4x://unit/2': [this.collection.at(3)],
                'i4x://unit/3': [this.collection.at(4)]
            };

            _.each(units, function(value, key) {
                compareUnits(structure.units[key], value);
            });
        });
    });
});
