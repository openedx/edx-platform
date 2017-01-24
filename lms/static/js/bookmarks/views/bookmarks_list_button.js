(function(define, undefined) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone', 'js/bookmarks/views/bookmarks_list',
            'js/bookmarks/collections/bookmarks', 'js/views/message_banner'],
        function(gettext, $, _, Backbone, BookmarksListView, BookmarksCollection, MessageBannerView) {
            return Backbone.View.extend({

                el: '.courseware-bookmarks-button',

                loadingMessageElement: '#loading-message',
                errorMessageElement: '#error-message',

                events: {
                    'click .bookmarks-list-button': 'toggleBookmarksListView'
                },

                initialize: function() {
                    var bookmarksCollection = new BookmarksCollection([],
                        {
                            course_id: $('.courseware-results').data('courseId'),
                            url: $('.courseware-bookmarks-button').data('bookmarksApiUrl')
                        }
                );
                    this.bookmarksListView = new BookmarksListView(
                        {
                            collection: bookmarksCollection,
                            loadingMessageView: new MessageBannerView({el: $(this.loadingMessageElement)}),
                            errorMessageView: new MessageBannerView({el: $(this.errorMessageElement)})
                        }
                );
                },

                toggleBookmarksListView: function() {
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
