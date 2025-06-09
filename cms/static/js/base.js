define([
    'domReady',
    'jquery',
    'underscore',
    'gettext',
    'common/js/components/views/feedback_notification',
    'common/js/components/views/feedback_prompt',
    'js/utils/date_utils',
    'js/utils/module',
    'js/utils/handle_iframe_binding',
    'edx-ui-toolkit/js/dropdown-menu/dropdown-menu-view',
    'jquery.ui',
    'jquery.leanModal',
    'jquery.form',
    'jquery.smoothScroll'
],
function(
    domReady,
    $,
    _,
    gettext,
    NotificationView,
    PromptView,
    DateUtils,
    ModuleUtils,
    IframeUtils,
    DropdownMenuView
) {
    'use strict';

    var $body;

    function smoothScrollLink(e) {
        (e).preventDefault();

        $.smoothScroll({
            offset: -200,
            easing: 'swing',
            speed: 1000,
            scrollElement: null,
            scrollTarget: $(this).attr('href')
        });
    }

    function hideNotification(e) {
        (e).preventDefault();
        $(this)
            .closest('.wrapper-notification')
            .removeClass('is-shown')
            .addClass('is-hiding')
            .attr('aria-hidden', 'true');
    }

    function hideAlert(e) {
        (e).preventDefault();
        $(this).closest('.wrapper-alert').removeClass('is-shown');
    }

    domReady(function() {
        var dropdownMenuView;

        $body = $('body');

        $body.on('click', '.embeddable-xml-input', function() {
            $(this).select();
        });

        $body.addClass('js');

        // alerts/notifications - manual close
        $('.action-alert-close, .alert.has-actions .nav-actions a').bind('click', hideAlert);
        $('.action-notification-close').bind('click', hideNotification);

        // nav - dropdown related
        $body.click(function() {
            // Reset iframe height to default when the XBlock action dropdown is closed
            if ($('.nav-dd .nav-item .wrapper-nav-sub.is-shown').length && window.self !== window.top) {
              try {
                window.parent.postMessage({
                  type: 'toggleCourseXBlockDropdown',
                  message: 'Adjust the height of the dropdown menu',
                  payload: { courseXBlockDropdownHeight: 0 }
                }, document.referrer);
              } catch (e) {
                console.error('Failed to post message:', e);
              }
            }
            $('.nav-dd .nav-item .wrapper-nav-sub').removeClass('is-shown');
            $('.nav-dd .nav-item .title').removeClass('is-selected');
            $('.custom-dropdown .dropdown-options').hide();
        });

        $('.nav-dd .nav-item, .filterable-column .nav-item').click(function(e) {
            var $subnav = $(this).find('.wrapper-nav-sub'),
                $title = $(this).find('.title');

            if ($subnav.hasClass('is-shown')) {
                $subnav.removeClass('is-shown');
                $title.removeClass('is-selected');
            } else {
                $('.nav-dd .nav-item .title').removeClass('is-selected');
                $('.nav-dd .nav-item .wrapper-nav-sub').removeClass('is-shown');
                $title.addClass('is-selected');
                $subnav.addClass('is-shown');
                // if propagation is not stopped, the event will bubble up to the
                // body element, which will close the dropdown.
                e.stopPropagation();
            }
        });

        // general link management - new window/tab
        $('a[rel="external"]:not([title])')
            .attr('title', gettext('This link will open in a new browser window/tab'));
        $('a[rel="external"]').attr({
            rel: 'noopener external',
            target: '_blank'
        });

        // general link management - lean modal window
        $('a[rel="modal"]').attr('title', gettext('This link will open in a modal window')).leanModal({
            overlay: 0.50,
            closeButton: '.action-modal-close'
        });
        $('.action-modal-close').click(function(e) {
            (e).preventDefault();
        });

        // general link management - smooth scrolling page links
        $('a[rel*="view"][href^="#"]').bind('click', smoothScrollLink);

        IframeUtils.iframeBinding();

        // disable ajax caching in IE so that backbone fetches work
        if ($.browser.msie) {
            $.ajaxSetup({cache: false});
        }

        // Initiate the edx tool kit dropdown menu
        if ($('.js-header-user-menu').length) {
            dropdownMenuView = new DropdownMenuView({
                el: '.js-header-user-menu'
            });
            dropdownMenuView.postRender();
        }

        window.studioNavMenuActive = true;
    });
}); // end require()
