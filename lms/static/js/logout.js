/**
 * JS for the logout page.
 *
 * This script waits for all iframes on the page to load before redirecting the user
 * to a specified URL. If there are no iframes on the page, the user is immediately redirected.
 */
(function($) {
    'use strict';

    $(function() {
        var $iframeContainer = $('#iframeContainer'),
            $iframes = $iframeContainer.find('iframe'),
            redirectUrl = $iframeContainer.data('redirect-url');

        if ($iframes.length === 0) {
            window.location = redirectUrl;
        }

        $iframes.allLoaded(function() {
            window.location = redirectUrl;
        });
    });
}(jQuery));
