;(function (define) {
'use strict';
define([
    'underscore', 'edx-ui-toolkit/js/pagination/paging-collection', 'js/edxnotes/models/note'
], function (_, PagingCollection, NoteModel) {
    return PagingCollection.extend({
        model: NoteModel,

        state: {
            pageSize: 10
        },

        queryParams: {},

        constructor: function (models, options) {
            this.url = options.url;
            this.state.pageSize = options.perPage;

            if (options.text) {
                this.queryParams.text = options.text;
            }

            PagingCollection.prototype.constructor.call(this, models, options);
        },

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

                return courseStructure;
            };
        }())
    });
});
}).call(this, define || RequireJS.define);
