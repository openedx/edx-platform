(function(define, undefined) {
    'use strict';
    define([
        'underscore', 'annotator_1.2.9'
    ], function(_, Annotator) {
    /**
     * Modifies Annotator.Plugin.Store.annotationCreated to make it trigger a new
     * event `annotationFullyCreated` when annotation is fully created and has
     * an id.
     */
        Annotator.Plugin.Store.prototype.annotationCreated = _.compose(
            function(jqXhr) {
                return jqXhr.done(_.bind(function(annotation) {
                    if (annotation && annotation.id) {
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
        Annotator.Plugin.Events = function() {
        // Call the Annotator.Plugin constructor this sets up the element and
        // options properties.
            Annotator.Plugin.apply(this, arguments);
        };

        _.extend(Annotator.Plugin.Events.prototype, new Annotator.Plugin(), {
            pluginInit: function() {
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

            destroy: function() {
                this.annotator
                    .unsubscribe('annotationViewerShown', this.annotationViewerShown)
                    .unsubscribe('annotationFullyCreated', this.annotationFullyCreated)
                    .unsubscribe('annotationEditorShown', this.annotationEditorShown)
                    .unsubscribe('annotationEditorHidden', this.annotationEditorHidden)
                    .unsubscribe('annotationUpdated', this.annotationUpdated)
                    .unsubscribe('annotationDeleted', this.annotationDeleted);
            },

            annotationViewerShown: function(viewer, annotations) {
            // Emits an event only when the annotation already exists on the
            // server. Otherwise, `annotation.id` is `undefined`.
                var data;
                annotations = _.reject(annotations, this.isNew);
                data = {
                    notes: _.map(annotations, function(annotation) {
                        return {note_id: annotation.id};
                    })
                };
                if (data.notes.length) {
                    this.log('edx.course.student_notes.viewed', data);
                }
            },

            annotationFullyCreated: function(annotation) {
                var data = this.getDefaultData(annotation);
                this.log('edx.course.student_notes.added', data);
            },

            annotationEditorShown: function(editor, annotation) {
                this.oldNoteText = annotation.text || '';
                this.oldTags = annotation.tags || [];
            },

            annotationEditorHidden: function() {
                this.oldNoteText = null;
                this.oldTags = null;
            },

            annotationUpdated: function(annotation) {
                var data, defaultData;
                if (!this.isNew(annotation)) {
                    defaultData = this.getDefaultData(annotation);
                    data = _.extend(
                        defaultData,
                        this.getText('old_note_text', this.oldNoteText, defaultData.truncated),
                        this.getTextArray('old_tags', this.oldTags, defaultData.truncated)
                    );
                    this.log('edx.course.student_notes.edited', data);
                }
            },

            annotationDeleted: function(annotation) {
                var data;
                // Emits an event only when the annotation already exists on the
                // server.
                if (!this.isNew(annotation)) {
                    data = this.getDefaultData(annotation);
                    this.log('edx.course.student_notes.deleted', data);
                }
            },

            getDefaultData: function(annotation) {
                var truncated = [];
                return _.extend(
                    {
                        note_id: annotation.id,
                        component_usage_id: annotation.usage_id,
                        truncated: truncated
                    },
                    this.getText('note_text', annotation.text, truncated),
                    this.getText('highlighted_content', annotation.quote, truncated),
                    this.getTextArray('tags', annotation.tags, truncated)
                );
            },

            getText: function(fieldName, text, truncated) {
                var info = {},
                    limit = this.options.stringLimit;

                if (_.isNumber(limit) && _.isString(text) && text.length > limit) {
                    text = String(text).slice(0, limit);
                    truncated.push(fieldName);
                }

                info[fieldName] = text;

                return info;
            },

            getTextArray: function(fieldName, textArray, truncated) {
                var info = {},
                    limit = this.options.stringLimit,
                    totalLength = 0,
                    returnArray = [],
                    i;

                if (_.isNumber(limit) && _.isArray(textArray)) {
                    for (i = 0; i < textArray.length; i++) {
                        if (_.isString(textArray[i]) && totalLength + textArray[i].length > limit) {
                            truncated.push(fieldName);
                            break;
                        }
                        totalLength += textArray[i].length;
                        returnArray[i] = textArray[i];
                    }
                } else {
                    returnArray = textArray;
                }

                info[fieldName] = returnArray;

                return info;
            },

            /**
         * If the model does not yet have an id, it is considered to be new.
         * @return {Boolean}
         */
            isNew: function(annotation) {
                return !_.has(annotation, 'id');
            },

            log: function(eventName, data) {
                this.annotator.logger.emit(eventName, data);
            }
        });
    });
}).call(this, define || RequireJS.define);
