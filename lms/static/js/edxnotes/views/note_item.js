;(function (define, gettext, undefined) {
    'use strict';
    define(['underscore', 'backbone'], function (_, Backbone) {
        var NoteItemView = Backbone.View.extend({
            tagName: 'article',
            className: 'edx-notes-page-item',
            id: function () {
                return 'edx-notes-page-item-' + _.uniqueId();
            },

            initialize: function (options) {
                this.template = _.template($('#note-item-tpl').text());
            },

            render: function () {
                var context = this.model.toJSON();
                this.$el.html(this.template(context));
                return this;
            },

            destroy: function () {
                this.remove();
            }
        });

        return NoteItemView;
    });
}).call(this, define || RequireJS.define, gettext);
