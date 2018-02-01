import 'jquery';
import MessageBannerView from 'js/views/message_banner';
import BookmarksCollection from './collections/bookmarks';
import BookmarksListView from './views/bookmarks_list';

function CourseBookmarksFactory(options) {
  const courseId = options.courseId;
  const bookmarksApiUrl = options.bookmarksApiUrl;
  const bookmarksCollection = new BookmarksCollection([], {
    course_id: courseId,
    url: bookmarksApiUrl,
  },
  );
  const bookmarksView = new BookmarksListView(
    {
      $el: options.$el,
      collection: bookmarksCollection,
      loadingMessageView: new MessageBannerView({ el: $('#loading-message') }),
      errorMessageView: new MessageBannerView({ el: $('#error-message') }),
    },
                );
  bookmarksView.render();
  bookmarksView.showBookmarks();
  return bookmarksView;
}

export default CourseBookmarksFactory;
