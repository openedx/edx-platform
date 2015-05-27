;(function (define, undefined) {
'use strict';
define([
    'jquery', 'js/edxnotes/collections/notes', 'js/edxnotes/views/notes_page'
], function ($, NotesCollection, NotesPageView) {
    /**
     * Factory method for the Notes page.
     * @param {Object} params Params for the Notes page.
     * @param {Array} params.notesList A list of note models.
     * @param {Boolean} params.debugMode Enable the flag to see debug information.
     * @param {String} params.endpoint The endpoint of the store.
     * @return {Object} An instance of NotesPageView.
     */
    return function (params) {
        var collection = new NotesCollection(params.notesList);

        return new NotesPageView({
            el: $('.wrapper-student-notes').get(0),
            collection: collection,
            debug: params.debugMode,
            endpoint: params.endpoint
        });
    };
});
}).call(this, define || RequireJS.define);
