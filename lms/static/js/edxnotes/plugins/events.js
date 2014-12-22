;(function (define, undefined) {
'use strict';
define([
    'underscore', 'annotator', 'underscore.string'
], function (_, Annotator) {
    /**
     * Modifies Annotator.Plugin.Store.annotationCreated to make it trigger a new
     * event `annotationFullyCreated` when annotation is fully created and has
     * an id.
     */
    Annotator.Plugin.Store.prototype.annotationCreated = _.compose(
        function (jqXhr) {
            return jqXhr.done(_.bind(function (annotation) {
                if (annotation && annotation.id){
                    this.publish('annotationFullyCreated', annotation);
                }
            }, this));
        },
        Annotator.Plugin.Store.prototype.annotationCreated
    );

    /**
     * Adds the Events Plugin which emits events to capture user intent.
     * Emits the following events:
     * - 'edx.course.student_notes.viewed'
     *   [(user, note ID, datetime), (user, note ID, datetime)] - a list of notes.
     * - 'edx.course.student_notes.added'
     *   (user, note ID, note text, highlighted content, ID of the component annotated, datetime)
     * - 'edx.course.student_notes.edited'
     *   (user, note ID, old note text, new note text, highlighted content, ID of the component annotated, datetime)
     * - 'edx.course.student_notes.deleted'
     *   (user, note ID, note text, highlighted content, ID of the component annotated, datetime)
     **/
    Annotator.Plugin.Events = function () {
        // Call the Annotator.Plugin constructor this sets up the element and
        // options properties.
        Annotator.Plugin.apply(this, arguments);
    };

    _.extend(Annotator.Plugin.Events.prototype, new Annotator.Plugin(), {
        stringLimit: 300,

        pluginInit: function () {
            _.bindAll(this,
                'annotationViewerShown', 'annotationFullyCreated', 'annotationEditorShown',
                'annotationEditorHidden', 'annotationUpdated', 'annotationDeleted'
            );

            this.annotator
                .subscribe('annotationViewerShown', this.annotationViewerShown)
                .subscribe('annotationFullyCreated', this.annotationFullyCreated)
                .subscribe('annotationEditorShown', this.annotationEditorShown)
                .subscribe('annotationEditorHidden', this.annotationEditorHidden)
                .subscribe('annotationUpdated', this.annotationUpdated)
                .subscribe('annotationDeleted', this.annotationDeleted);
        },

        destroy: function () {
            this.annotator
                .unsubscribe('annotationViewerShown', this.annotationViewerShown)
                .unsubscribe('annotationFullyCreated', this.annotationFullyCreated)
                .unsubscribe('annotationEditorShown', this.annotationEditorShown)
                .unsubscribe('annotationEditorHidden', this.annotationEditorHidden)
                .unsubscribe('annotationUpdated', this.annotationUpdated)
                .unsubscribe('annotationDeleted', this.annotationDeleted);
        },

        annotationViewerShown: function (viewer, annotations) {
            var data = {
                'notes': _.map(annotations, function (annotation) {
                    return {'note_id': annotation.id};
                })
            };
            this.log('edx.course.student_notes.viewed', data);
        },

        annotationFullyCreated: function (annotation) {
            var data = this.getDefaultData(annotation);
            this.log('edx.course.student_notes.added', data);
        },

        annotationEditorShown: function (editor, annotation) {
            this.oldNoteText = annotation.text;
        },

        annotationEditorHidden: function () {
            this.oldNoteText = null;
        },

        annotationUpdated: function (annotation) {
            var data = _.extend({
                old_note_text: _.str.truncate(this.oldNoteText, this.stringLimit)
            }, this.getDefaultData(annotation));
            this.log('edx.course.student_notes.edited', data);
        },

        annotationDeleted: function (annotation) {
            var data = this.getDefaultData(annotation);
            this.log('edx.course.student_notes.deleted', data);
        },

        getDefaultData: function (annotation) {
            return {
                'note_id': annotation.id,
                'note_text': _.str.truncate(annotation.text, this.stringLimit),
                'highlighted_content': _.str.truncate(annotation.quote, this.stringLimit),
                'component_id': annotation.usage_id
            };
        },

        log: function (eventName, data) {
            this.annotator.logger.emit(eventName, data);
        }
    });
});
}).call(this, define || RequireJS.define);
