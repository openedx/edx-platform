define(['js/edxnotes/collections/notes'], function(NotesCollection) {
    'use strict';
    describe('EdxNotes NotesCollection', function() {
        var getChapter, getSection, getUnit, notes;

        getChapter = function (name, location, index, children) {
            return {
                display_name: name,
                location: 'i4x://chapter/' + location,
                index: index,
                children: _.map(children, function (i) {
                    return 'i4x://section/' + i;
                })
            };
        };

        getSection = function (name, location, children) {
            return {
                display_name: name,
                location: 'i4x://section/' + location,
                children: _.map(children, function (i) {
                    return 'i4x://unit/' + i;
                })
            };
        };

        getUnit = function (name, location) {
            return {
                display_name: name,
                location: 'i4x://unit/' + location,
                url: 'http://example.com'
            };
        };

        notes = [
            {
                chapter: getChapter('Second Chapter', 0, 1, [1, 'w_n', 0]),
                section: getSection('Third Section', 0, ['w_n', 1, 0]),
                unit: getUnit('Fourth Unit', 0),
                created: 'December 11, 2014 at 11:12AM',
                updated: 'December 11, 2014 at 11:12AM',
                text: 'Third added model',
                quote: 'Note 4'
            },
            {
                chapter: getChapter('Second Chapter', 0, 1, [1, 'w_n', 0]),
                section: getSection('Third Section', 0, ['w_n', 1, 0]),
                unit: getUnit('Fourth Unit', 0),
                created: 'December 11, 2014 at 11:11AM',
                updated: 'December 11, 2014 at 11:11AM',
                text: 'Third added model',
                quote: 'Note 5'
            },
            {
                chapter: getChapter('Second Chapter', 0, 1, [1, 'w_n', 0]),
                section: getSection('Third Section', 0, ['w_n', 1, 0]),
                unit: getUnit('Third Unit', 1),
                created: 'December 11, 2014 at 11:11AM',
                updated: 'December 11, 2014 at 11:11AM',
                text: 'Second added model',
                quote: 'Note 3'
            },
            {
                chapter: getChapter('Second Chapter', 0, 1, [1, 'w_n', 0]),
                section: getSection('Second Section', 1, [2]),
                unit: getUnit('Second Unit', 2),
                created: 'December 11, 2014 at 11:10AM',
                updated: 'December 11, 2014 at 11:10AM',
                text: 'First added model',
                quote: 'Note 2'
            },
            {
                chapter: getChapter('First Chapter', 1, 0, [2]),
                section: getSection('First Section', 2, [3]),
                unit: getUnit('First Unit', 3),
                created: 'December 11, 2014 at 11:10AM',
                updated: 'December 11, 2014 at 11:10AM',
                text: 'First added model',
                quote: 'Note 1'
            }
        ];

        beforeEach(function () {
            this.collection = new NotesCollection(notes);
        });

        it('can return correct course structure', function () {
            var structure = this.collection.getCourseStructure();


            expect(structure.chapters).toEqual([
                getChapter('First Chapter', 1, 0, [2]),
                getChapter('Second Chapter', 0, 1, [1, 'w_n', 0])
            ]);

            expect(structure.sections).toEqual({
                'i4x://section/0': getSection('Third Section', 0, ['w_n', 1, 0]),
                'i4x://section/1': getSection('Second Section', 1, [2]),
                'i4x://section/2': getSection('First Section', 2, [3])
            });

            expect(structure.units).toEqual({
                'i4x://unit/0': [this.collection.at(0), this.collection.at(1)],
                'i4x://unit/1': [this.collection.at(2)],
                'i4x://unit/2': [this.collection.at(3)],
                'i4x://unit/3': [this.collection.at(4)]
            });
        });
    });
});
