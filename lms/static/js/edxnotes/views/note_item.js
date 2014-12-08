;(function (define, undefined) {
'use strict';
define([
    'jquery', 'backbone'
], function ($, Backbone) {
    var NoteItemView = Backbone.View.extend({
        tagName: 'article',
        id: function () {
            return 'note-' + _.uniqueId();
        },
        className: 'note',
        events: {
            'click .note-excerpt-more-link': 'moreHandler'
        },

        initialize: function (options) {
            var templateSelector = '#note-item-tpl',
                templateText = $(templateSelector).text();

            if (!templateText) {
                console.error('Failed to load note-item template');
            }

            this.template = _.template(templateText);
            this.listenTo(this.model, 'change:is_expanded', this.render);
        },

        render: function () {
            var context = this.getContext();
            this.$el.html(this.template(context));

            return this;
        },

        getContext: function () {
            return $.extend({}, this.model.attributes, {
                message: this.model.getNoteText()
            });
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
