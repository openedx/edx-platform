/**
 * Provides utilities to open and close the tagging drawer to manage tags.
 * 
 * To use this drawer you need to add the following code into your template:
 * 
 * ```
 * <div id="manage-tags-drawer" class="drawer"></div>
 * <div class="drawer-cover"></div>
 * ```
 */
define(['jquery'],
function($) {
    'use strict';

    var closeDrawer, openDrawer;

    closeDrawer = function(drawer, drawerCover) {
        $(drawerCover).css('display', 'none');
        $(drawer).empty();
        $(drawer).css('display', 'none');
        $('body').removeClass('drawer-open');
    };

    openDrawer = function(taxonomyTagsWidgetUrl, contentId) {
        const drawer = document.querySelector("#manage-tags-drawer");
        const drawerCover = document.querySelector(".drawer-cover");

        // Add event listen to close drawer when close button is clicked from within the Iframe
        window.addEventListener("message", function (event) {
            if (event.data === 'closeManageTagsDrawer') {
                closeDrawer(drawer, drawerCover)
            }
        }.bind(this));

        $(drawerCover).css('display', 'block');
        // xss-lint: disable=javascript-jquery-html
        $(drawer).html(
            `<iframe src="${taxonomyTagsWidgetUrl}${contentId}" onload="this.contentWindow.focus()" frameborder="0" style="width: 100%; height: 100%;"></iframe>`
        );
        $(drawer).css('display', 'block');

        // Prevent background from being scrollable when drawer is open
        $('body').addClass('drawer-open');
    };

    return {
        openDrawer: openDrawer,
        closeDrawer: closeDrawer
    };
});
