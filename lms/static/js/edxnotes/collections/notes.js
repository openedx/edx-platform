;(function (define, undefined) {
'use strict';
define([
    'backbone', 'js/edxnotes/models/note'
], function (Backbone, NoteModel) {
    var NotesCollection = Backbone.Collection.extend({
        model: NoteModel,

        /**
         * Returns course structure from the list of notes.
         * @return {Object}
         */
        getCourseStructure: (function () {
            var courseStructure = null;
            return function () {
                var chapters = {},
                    sections = {},
                    units = {};

                if (!courseStructure) {
                    this.each(function (note) {
                        var chapter = note.get('chapter'),
                            section = note.get('section'),
                            unit = note.get('unit');

                        chapters[chapter.location] = chapter;
                        sections[section.location] = section;
                        units[unit.location] = units[unit.location] || [];
                        units[unit.location].push(note);
                    });

                    courseStructure = {
                        chapters: _.sortBy(_.toArray(chapters), function (c) {return c.index;}),
                        sections: sections,
                        units: units
                    };
                }

                return courseStructure;
            };
        }())
    });

    return NotesCollection;
});
}).call(this, define || RequireJS.define);
