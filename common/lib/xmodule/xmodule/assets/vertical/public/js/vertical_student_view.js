/* JavaScript for Vertical Student View. */
window.VerticalStudentView = function (runtime, element) {
    "use strict";
    if (typeof RequireJS === "undefined") {
        console.log("Cannot initialize VerticalStudentView. RequireJS is not defined.");
        return;
    }
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
};
