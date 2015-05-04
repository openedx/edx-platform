;(function (define, undefined) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone', 'js/bookmarks/views/bookmarks_list',
            'js/bookmarks/collections/bookmarks', 'js/views/message'],
        function (gettext, $, _, Backbone, BookmarksListView, BookmarksCollection, MessageView) {

        return Backbone.View.extend({

            el: '.courseware-bookmarks-button',

            loadingMessageElement: '#loading-message',
            errorMessageElement: '#error-message',

            events: {
                'click .bookmarks-list-button': 'toggleBookmarksListView'
            },

            initialize: function () {
                this.template = _.template($('#bookmarks_button-tpl').text());

                this.bookmarksListView = new BookmarksListView({
                    collection: new BookmarksCollection(),
                    loadingMessageView: new MessageView({el: $(this.loadingMessageElement)}),
                    errorMessageView: new MessageView({el: $(this.errorMessageElement)})
                });
            },


            toggleBookmarksListView: function () {
                if (this.bookmarksListView.areBookmarksVisible()) {
                    this.bookmarksListView.hideBookmarks();
                    this.$('.bookmarks-list-button').attr('aria-pressed', 'false');
                    this.$('.bookmarks-list-button').removeClass('is-active').addClass('is-inactive');
                } else {
                    this.bookmarksListView.showBookmarks();
                    this.$('.bookmarks-list-button').attr('aria-pressed', 'true');
                    this.$('.bookmarks-list-button').removeClass('is-inactive').addClass('is-active');
                }
            }
        });
    });
}).call(this, define || RequireJS.define);
