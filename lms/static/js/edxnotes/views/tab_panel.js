;(function (define, undefined) {
'use strict';
define(['gettext', 'underscore', 'backbone', 'js/edxnotes/views/note_item'],
function (gettext, _, Backbone, NoteItemView) {
    var TabPanelView = Backbone.View.extend({
        tagName: 'section',
        className: 'tab-panel',
        title: '',
        titleTemplate: _.template('<h2 class="sr"><%- text %></h2>'),
        attributes: {
            'tabindex': -1
        },

        initialize: function () {
            this.notes = [];
        },

        render: function () {
            this.$el.html(this.getTitle());
            this.renderContent();
            return this;
        },

        renderContent: function () {
            return this;
        },

        getNotes: function (collection) {
            var container = document.createDocumentFragment();
            this.notes = _.each(collection, function (model) {
                var note = new NoteItemView({model: model});
                container.appendChild(note.render().el);
                return note;
            });
            return container;
        },

        getTitle: function () {
            return this.title ? this.titleTemplate({text: gettext(this.title)}) : '';
        },

        remove: function () {
            _.invoke(this.notes, 'remove');
            this.notes = [];
            Backbone.View.prototype.remove.call(this);
            return this;
        }
    });

    return TabPanelView;
});
}).call(this, define || RequireJS.define);
