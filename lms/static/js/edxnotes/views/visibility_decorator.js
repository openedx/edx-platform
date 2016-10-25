(function(define, undefined) {
    'use strict';
    define([
        'jquery', 'underscore', 'js/edxnotes/views/notes_factory'
    ], function($, _, NotesFactory) {
        var parameters = {}, visibility = null,
            getIds, createNote, cleanup, factory, annotatorContainerElement, getAnnotatableComponentsIds;

        getIds = function() {
            return [annotatorContainerElement.id];
        };

        getAnnotatableComponentsIds = function () {
            return _.map($('.edx-notes-wrapper'), function(element){return $(element).data('usageId')});
        };

        createNote = function(params) {
            if (params) {
                return NotesFactory.factory(annotatorContainerElement, params, getAnnotatableComponentsIds());
            }
            return null;
        };

        cleanup = function(ids) {
            var list = _.clone(Annotator._instances);
            ids = ids || [];

            _.each(list, function(instance) {
                var id = instance.element.attr('id');
                if (!_.contains(ids, id)) {
                    instance.destroy();
                }
            });
        };

        factory = function(containerElement, params) {
            debugger;
            // When switching sequentials, we need to keep track of the
            // parameters of each element and the visibility (that may have been
            // changed by the checkbox).
            annotatorContainerElement = containerElement
            parameters = params || parameters;

            if (_.isNull(visibility)) {
                visibility = params.isVisible;
            }

            if (visibility) {
                // When switching sequentials, the global object Annotator still
                // keeps track of the previous instances that were created in an
                // array called 'Annotator._instances'. We have to destroy these
                // but keep those found on page being loaded (for the case when
                // there are more than one HTMLcomponent per vertical).
                cleanup(getIds());
                return createNote(parameters);
            }
            return null;
        };

        return {
            factory: factory,

            enableNote: function() {
                createNote(parameters);
                visibility = true;
            },

            disableNotes: function() {
                cleanup();
                visibility = false;
            },

            _setVisibility: function(state) {
                visibility = state;
            }
        };
    });
}).call(this, define || RequireJS.define);
