;(function (define, undefined) {
'use strict';
define([
    'backbone', 'js/edxnotes/models/note'
], function (Backbone, NoteModel) {
    var NotesCollection = Backbone.Collection.extend({
        model: NoteModel,

        getSortedByCourseStructure: (function () {
            var sortedCollection = null;
            return function () {
                if (!sortedCollection) {
                    sortedCollection = this.sortBy(function (note) {
                        var index = '';
                            index += note.get('chapter').index;
                            index += note.get('section').index;
                            index += note.get('unit').index;

                        return Number(index);
                    });
                }

                return sortedCollection;
            };
        }())
    });

    return NotesCollection;
});
}).call(this, define || RequireJS.define);
