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
            this.children = [];
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
            var container = document.createDocumentFragment(), scrollToTag = this.options.scrollToTag, view = this.title,
                notes = _.map(collection, function (model) {
                    var note = new NoteItemView({model: model, scrollToTag: scrollToTag, view: view});
                    container.appendChild(note.render().el);
                    return note;
                });

            this.children = this.children.concat(notes);
            return container;
        },

        getTitle: function () {
            return this.title ? this.titleTemplate({text: gettext(this.title)}) : '';
        },

        remove: function () {
            _.invoke(this.children, 'remove');
            this.children = null;
            Backbone.View.prototype.remove.call(this);
            return this;
        }
    });

    return TabPanelView;
});
}).call(this, define || RequireJS.define);
