/* JavaScript for Vertical Student View. */

/* global Set:false */  // false means do not assign to Set

// The vertical marks blocks complete if they are completable by viewing.  The
// global variable SEEN_COMPLETABLES tracks blocks between separate loads of
// the same vertical (when a learner goes from one tab to the next, and then
// navigates back within a given sequential) to protect against duplicate calls
// to the server.

var SEEN_COMPLETABLES = new Set();

window.VerticalStudentView = function(runtime, element) {
    'use strict';
    RequireJS.require(['course_bookmarks/js/views/bookmark_button'], function(BookmarkButton) {
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
    $(element).find('.vert').each(
        function(idx, block) {
            var blockKey = block.dataset.id;

            if (!block.dataset.completableByViewing) {
                return;
            }
            // TODO: EDUCATOR-1778
            // *  Check if blocks are in the browser's view window or in focus
            //    before marking complete. This will include a configurable
            //    delay so that blocks must be seen for a few seconds before
            //    being marked complete, to prevent completion via rapid
            //    scrolling.  (OC-3358)
            // *  Limit network traffic by batching and throttling calls.
            //    (OC-3090)
            if (blockKey && !SEEN_COMPLETABLES.has(blockKey)) {
                $.ajax({
                    type: 'POST',
                    url: runtime.handlerUrl(element, 'publish_completion'),
                    data: JSON.stringify({
                        block_key: blockKey,
                        completion: 1.0
                    })
                });
                SEEN_COMPLETABLES.add(blockKey);
            }
        }
    );
};
