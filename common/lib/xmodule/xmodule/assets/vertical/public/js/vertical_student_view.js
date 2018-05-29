/* JavaScript for Vertical Student View. */

/* global Set:false */ // false means do not assign to Set

// The vertical marks blocks complete if they are completable by viewing.  The
// global variable SEEN_COMPLETABLES tracks blocks between separate loads of
// the same vertical (when a learner goes from one tab to the next, and then
// navigates back within a given sequential) to protect against duplicate calls
// to the server.

import BookmarkButton from 'course_bookmarks/js/views/bookmark_button';
import {ViewedEventTracker} from '../../../../../../../../lms/static/completion/js/ViewedEvent.js';

var SEEN_COMPLETABLES = new Set();

window.VerticalStudentView = function(runtime, element) {
    'use strict';
    var $element = $(element);
    var $bookmarkButtonElement = $element.find('.bookmark-button');
    return new BookmarkButton({
        el: $bookmarkButtonElement,
        bookmarkId: $bookmarkButtonElement.data('bookmarkId'),
        usageId: $element.data('usageId'),
        bookmarked: $element.parent('#seq_content').data('bookmarked'),
        apiUrl: $bookmarkButtonElement.data('bookmarksApiUrl')
    });

    var tracker, vertical, viewedAfter;
    var completableBlocks = [];
    var vertModDivs = element.getElementsByClassName('vert-mod');
    if (vertModDivs.length === 0) {
        return;
    }
    vertical = vertModDivs[0];
    $(element).find('.vert').each(function(idx, block) {
        if (block.dataset.completableByViewing !== undefined) {
            completableBlocks.push(block);
        }
    });
    if (completableBlocks.length > 0) {
        viewedAfter = parseInt(vertical.dataset.completionDelayMs, 10);
        if (!(viewedAfter >= 0)) {
            // parseInt will return NaN if it fails to parse, which is not >= 0.
            viewedAfter = 5000;
        }
        tracker = new ViewedEventTracker(completableBlocks, viewedAfter);
        tracker.addHandler(function(block, event) {
            var blockKey = block.dataset.id;

            if (blockKey && !SEEN_COMPLETABLES.has(blockKey)) {
                if (event.elementHasBeenViewed) {
                    $.ajax({
                        type: 'POST',
                        url: runtime.handlerUrl(element, 'publish_completion'),
                        data: JSON.stringify({
                            block_key: blockKey,
                            completion: 1.0
                        })
                    }).then(
                        function() {
                            SEEN_COMPLETABLES.add(blockKey);
                        }
                    );
                }
            }
        });
    }
};
