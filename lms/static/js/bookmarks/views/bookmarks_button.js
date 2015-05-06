;(function (define, undefined) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone', 'js/bookmarks/views/bookmarks_results',
            'js/bookmarks/collections/bookmarks'],
        function (gettext, $, _, Backbone, BookmarksResultsView, BookmarksCollection) {

        var BookmarksButtonView = Backbone.View.extend({

            el: '.courseware-bookmarks-button',

            events: {
                'click .bookmarks-button': 'toggleBookmarksListView'
            },

            initialize: function () {
                this.template = _.template($('#bookmarks_button-tpl').text());
                this.bookmarksResultsView = new BookmarksResultsView({collection: new BookmarksCollection()});
                _.bindAll(this, 'render');
            },

            render: function () {
                this.$el.html(this.template({}));
                return this;
            },

            toggleBookmarksListView: function () {
                if (this.bookmarksResultsView.bookmarksShown()) {
                    this.bookmarksResultsView.hideBookmarks();
                    this.$('.bookmarks-button').attr('aria-pressed', 'false');
                } else {
                    this.bookmarksResultsView.loadBookmarks();
                    this.$('.bookmarks-button').attr('aria-pressed', 'true');
                }
            }
        });

        return BookmarksButtonView;
    });
}).call(this, define || RequireJS.define);
