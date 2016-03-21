/* JavaScript for Vertical Student View. */
window.VerticalStudentView = function (runtime, element) {

    'use strict';
    RequireJS.require(['js/bookmarks/views/bookmark_button'], function (BookmarkButton) {
        var $element = $(element);
        var $bookmarkButtonElement = $element.find('.bookmark-button');

        return new BookmarkButton({
            el: $bookmarkButtonElement,
            bookmarkId: $bookmarkButtonElement.data('bookmarkId'),
            usageId: $element.data('usageId'),
            bookmarked: $element.parent('#seq_content').data('bookmarked'),
            apiUrl: $(".courseware-bookmarks-button").data('bookmarksApiUrl')
        });
    });
    RequireJS.require(['js/fullscreen/views/fullscreen_button'], function (FullscreenButton) {
        var $element = $(element);
        var $fullscreenButtonElement = $element.find('.fullscreen-button');

        return new FullscreenButton({
            el: $fullscreenButtonElement,
        });
    });
};
