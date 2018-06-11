/* JavaScript for Vertical Student View. */

/* global markBlocksCompletedOnViewIfNeeded:false */

window.VerticalStudentView = function(runtime, element) {
    'use strict';

    markBlocksCompletedOnViewIfNeeded(runtime, element);

    if (typeof RequireJS === 'undefined') {
        // eslint-disable-next-line no-console
        console.warn('Cannot initialize bookmarks for VerticalStudentView. RequireJS is not defined.');
        return;
    }
    RequireJS.require(['js/bookmarks/views/bookmark_button'], function(BookmarkButton) {
        var $element = $(element);
        var $bookmarkButtonElement = $element.find('.bookmark-button');

        return new BookmarkButton({
            el: $bookmarkButtonElement,
            bookmarkId: $bookmarkButtonElement.data('bookmarkId'),
            usageId: $element.data('usageId'),
            bookmarked: $element.parent('#seq_content').data('bookmarked'),
            apiUrl: $bookmarkButtonElement.data('bookmarksApiUrl')
        });
    });
};
