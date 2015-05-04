;(function (define, undefined) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone', 'js/bookmarks/views/bookmarks_results',
            'js/bookmarks/collections/bookmarks'],
        function (gettext, $, _, Backbone, BookmarksResultsView, BookmarksCollection) {

        var BookmarksButtonView = Backbone.View.extend({

            el: '.courseware-bookmarks-button',

            events: {
                'click .bookmarks-button': 'renderBookmarksListView'
            },

            initialize: function () {
                this.template = _.template($('#bookmarks_button-tpl').text());
                _.bindAll(this, 'render');
            },

            render: function () {
                this.$el.html(this.template({}));
                return this;
            },

            renderBookmarksListView: function () {
                var bookmarksCollection = new BookmarksCollection();
                new BookmarksResultsView({collection: bookmarksCollection}).loadBookmarks();
            }
        });

        return BookmarksButtonView;
    });
}).call(this, define || RequireJS.define);
