;(function (define, undefined) {
'use strict';
define([
    'jquery', 'backbone', 'js/edxnotes/utils/template'
], function ($, Backbone, templateUtils) {
    var NoteItemView = Backbone.View.extend({
        tagName: 'article',
        className: 'note',
        id: function () {
            return 'note-' + _.uniqueId();
        },
        events: {
            'click .note-excerpt-more-link': 'moreHandler'
        },

        initialize: function (options) {
            this.template = templateUtils.loadTemplate('note-item');
            this.listenTo(this.model, 'change:is_expanded', this.render);
        },

        render: function () {
            var context = this.getContext();
            this.$el.html(this.template(context));

            return this;
        },

        getContext: function () {
            return $.extend({
                message: this.model.getNoteText()
            }, this.model.toJSON());
        },

        toggleNote: function () {
            var value = !this.model.get('is_expanded');
            this.model.set('is_expanded', value);
        },

        moreHandler: function (event) {
            event.preventDefault();
            this.toggleNote();
        }
    });

    return NoteItemView;
});
}).call(this, define || RequireJS.define);
