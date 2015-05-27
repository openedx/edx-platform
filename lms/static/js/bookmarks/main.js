RequireJS.require([
    'js/bookmarks/views/bookmarks_button',
    'js/bookmarks/bookmark-button'
], function (BookmarksButton, BookmarkButton) {
    'use strict';

    new BookmarkButton();
    return new BookmarksButton();
});
