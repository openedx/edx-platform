;(function (define, undefined) {
'use strict';
define(['underscore', 'backbone', 'js/edxnotes/utils/logger'], function (_, Backbone, NotesLogger) {
    var TabModel = Backbone.Model.extend({
        defaults: {
            'identifier': '',
            'name': '',
            'icon': '',
            'is_active': false,
            'is_closable': false,
            'view': ''
        },

        initialize: function () {
            this.logger = NotesLogger.getLogger('tab');
        },

        activate: function () {
            this.collection.each(_.bind(function(model) {
                // Inactivate all other models.
                if (model !== this) {
                    model.inactivate();
                }
            }, this));
            this.set('is_active', true);
            this.logger.emit('edx.course.student_notes.notes_page_viewed', {
                'view': this.get('view')
            });
        },

        inactivate: function () {
            this.set('is_active', false);
        },

        isActive: function () {
            return this.get('is_active');
        }
    });

    return TabModel;
});
}).call(this, define || RequireJS.define);
