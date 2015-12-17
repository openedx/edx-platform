;(function (define) {
'use strict';
define([
    'underscore', 'common/js/components/collections/paging_collection', 'js/edxnotes/models/note'
], function (_, PagingCollection, NoteModel) {
    return PagingCollection.extend({
        model: NoteModel,

        initialize: function(models, options) {
            PagingCollection.prototype.initialize.call(this);

            this.perPage = options.perPage;
            this.server_api = _.extend(
                {'text': options.text ? options.text : null}, PagingCollection.prototype.server_api
            );

            // delete text query param if null
            if (this.server_api.text === null) {
                delete this.server_api.text;
            }

            // These are not specified for the Notes API
            delete this.server_api.sort_order;
            delete this.server_api.text_search;
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
});
}).call(this, define || RequireJS.define);
