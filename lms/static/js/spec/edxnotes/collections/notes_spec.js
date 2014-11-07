define(['js/edxnotes/collections/notes'],
    function(NotesCollection) {
        'use strict';

        describe('NotesCollection', function() {
            var collection;

            beforeEach(function() {
                collection = new NotesCollection([
                    {
                        updated: '2014-10-10T10:10:10.012+00:00',
                        text: 'Third listed'
                    },
                    {
                        updated: '2014-10-10T10:10:10.010+00:00',
                        text: 'First listed'
                    },
                    {
                        updated: '2014-10-10T10:10:10.011+00:00',
                        text: 'Second listed'
                    }
                ], {parse: true});
            });

            describe('Basic', function() {
                it('should order notes in ascending date', function() {
                    expect(collection.at(0).get('text')).toBe('First listed');
                    expect(collection.at(1).get('text')).toBe('Second listed');
                    expect(collection.at(2).get('text')).toBe('Third listed');
                });
            });
        });
    }
);
