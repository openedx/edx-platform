;(function (define, undefined) {
    'use strict';
    define([
        'jquery', 'js/edxnotes/collections/notes', 'js/edxnotes/views/notes_page'
    ], function ($, NotesCollection, NotesPageView) {
        /**
         * Factory method for the Notes page.
         * @param {Object} params Params for the Notes page.
         * @param {Array} params.notesList A list of note models.
         * @param {Boolean} params.debugMode The flag
         * @param {String} params.authToken An authentication token for the edx-notes-api.
         * @param {String} params.user User id of notes owner.
         * @param {String} params.courseId Course id.
         * @param {String} params.endpoint The endpoint of the store.
         * @return {Object} An instance of NotesPageView.
         */
        return function (params) {
            var collection = new NotesCollection(params.notesList, {parse: true});

            return new NotesPageView({
                el: $('.edx-notes-page-wrapper'),
                collection: collection,
                debug: params.debugMode,
                authToken: params.authToken,
                user: params.user,
                courseId: params.courseId,
                endpoint: params.endpoint
            }).render();
        };
    });
}).call(this, define || RequireJS.define);
