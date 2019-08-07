(function(define) {
    'use strict';

    define(
        [
            'jquery',
            'js/views/message_banner',
            'course_bookmarks/js/collections/bookmarks',
            'course_bookmarks/js/views/bookmarks_list'
        ],
        function($, MessageBannerView, BookmarksCollection, BookmarksListView) {
            return function(options) {
                var courseId = options.courseId,
                    bookmarksApiUrl = options.bookmarksApiUrl,
                    bookmarksCollection = new BookmarksCollection([],
                        {
                            course_id: courseId,
                            url: bookmarksApiUrl
                        }
                    );
                var bookmarksView = new BookmarksListView(
                    {
                        $el: options.$el,
                        collection: bookmarksCollection,
                        loadingMessageView: new MessageBannerView({el: $('#loading-message')}),
                        errorMessageView: new MessageBannerView({el: $('#error-message')})
                    }
                );
                bookmarksView.render();
                bookmarksView.showBookmarks();
                return bookmarksView;
            };
        }
    );
}).call(this, define || RequireJS.define);
