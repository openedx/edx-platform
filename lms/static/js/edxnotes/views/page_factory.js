(function(define, undefined) {
    'use strict';
    define([
        'jquery', 'js/edxnotes/collections/notes', 'js/edxnotes/views/notes_page'
    ], function($, NotesCollection, NotesPageView) {
    /**
     * Factory method for the Notes page.
     * @param {Object} params Params for the Notes page.
     * @param {List} params.disabledTabs Names of disabled tabs, these tabs will not be shown.
     * @param {Object} params.notes Paginated notes info.
     * @param {Number} params.pageSize Number of notes per page.
     * @param {Boolean} params.debugMode Enable the flag to see debug information.
     * @param {String} params.endpoint The endpoint of the store.
     * @return {Object} An instance of NotesPageView.
     */
        return function(params) {
            var collection = new NotesCollection(
            params.notes,
                {
                    url: params.notesEndpoint,
                    perPage: params.pageSize,
                    parse: true
                }
        );

            return new NotesPageView({
                el: $('.wrapper-student-notes').get(0),
                collection: collection,
                debug: params.debugMode,
                perPage: params.pageSize,
                disabledTabs: params.disabledTabs
            });
        };
    });
}).call(this, define || RequireJS.define);
