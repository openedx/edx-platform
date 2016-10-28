(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'annotator_1.2.9'], function($, _, Annotator) {
        var cleanup,
            renderNotes,
            fetchNotesWhenReady,
            storeNotesRequestData,
            searchRequestsData = [];

        /**
         * Clears the searchRequestsData.
         */
        cleanup = function() {
            searchRequestsData = [];
        };

        /**
         * Store requests data for each annotable component and fetch
         * notes for them when request for each component is stored.
         *
         * @param {object} data Request data for each annotable component
         */
        storeNotesRequestData = function(data) {
            searchRequestsData.push(data);
            fetchNotesWhenReady();
        };

        /**
         * Fetch notes for annotable components only when desired
         * number of requests are stored.
         *
         */
        fetchNotesWhenReady = function() {
            var settings,
                usageIds,
                searchEndpoint;

            if ($('.edx-notes-wrapper').length !== searchRequestsData.length) {
                return;
            }

            // `user` and `course_id` values are same for every annotatable
            // component so we pick these from first `searchRequestsData` item
            settings = {
                data: {
                    user: searchRequestsData[0].params.user,
                    course_id: searchRequestsData[0].params.courseId
                },
                type: 'GET',
                dataType: 'json',
                headers: {'x-annotator-auth-token': searchRequestsData[0].params.token}
            };
            searchEndpoint = searchRequestsData[0].params.endpoint + 'search/?';
            usageIds = _.map(searchRequestsData, function(item) {
                return 'usage_id=' + encodeURIComponent(item.params.usageId);
            });

            // Search endpoint expects the below format for query params
            // /api/v1/search/?course_id={course_id}&user={user_id}&usage_id={usage_id}&usage_id={usage_id} ...
            searchEndpoint += usageIds.join('&');

            $.ajax(
                searchEndpoint,
                settings
            )
            .done(function(jqXHR, textStatus, errorThrown) {
                renderNotes(jqXHR, textStatus, errorThrown);
            })
            .fail(function(jqXHR) {
                // `_action` is used by AnnotatorJS to construct error message
                jqXHR._action = 'search';  // eslint-disable-line no-underscore-dangle, no-param-reassign
                Annotator.Plugin.Store.prototype._onError(jqXHR);  // eslint-disable-line no-underscore-dangle
            })
            .always(function() {
                cleanup();
            });
        };

        /**
         * Pass notes to AnnotatorJS for rendering
         *
         * @param {Array} notes Notes data received from server
         */
        renderNotes = function(notes) {
            var edxNotes = {};

            // AnnotatorJS expects notes to be present in an array named as `rows`
            _.each(searchRequestsData, function(item) {
                edxNotes[item.params.usageId] = {rows: []};
            });

            // Place the received notes in the format below
            // edxNotes = {
            //     'usage_id1': [noteObject, noteObject, noteObject],
            //     'usage_id2': [noteObject, noteObject]
            // }
            _.each(notes, function(note) {
                edxNotes[note.usage_id].rows.push(note);
            });

            // Render the notes for each annotatable component using its associated AnnotatorJS instance
            _.each(searchRequestsData, function(item) {
                item.annotator.plugins.Store._onLoadAnnotationsFromSearch( // eslint-disable-line no-underscore-dangle
                    edxNotes[item.params.usageId]
                );
            });
        };

        return {
            storeNotesRequestData: storeNotesRequestData,
            cleanup: cleanup
        };
    });
}).call(this, define || RequireJS.define);
