/**
 * Modal for displaying the Terms of Service in the Register page.
 */

(function($, gettext) {
    'use strict';

    var focusableElementsSelector = [
        'a[href], area[href], input:not([disabled]), select:not([disabled]),',
        'textarea:not([disabled]), button:not([disabled]), iframe, object, embed,',
        '*[tabindex], *[contenteditable]'
    ].join(' ');

    var disableTabIndexingOn = function(containerSelector) {
        var $container = $(containerSelector),
            $focusableItems = $container.find('*').filter(focusableElementsSelector).filter(':visible');
        $container.attr('aria-hidden', 'true');
        $focusableItems.attr('tabindex', '-1');
    };

    var enableTabIndexingOn = function(containerSelector) {
        var $container = $(containerSelector),
            $focusableItems = $container.find('*').filter(focusableElementsSelector).filter(':visible');
        $container.attr('aria-hidden', 'false');
        $focusableItems.attr('tabindex', '0');
    };

    var showModal = function(modalSelector) {
        $(modalSelector).attr('aria-hidden', 'false');
        $(modalSelector).show();
        disableTabIndexingOn('.window-wrap');
        // Prevent scrolling of the background
        $('body').addClass('open-modal');
    };

    var hideModal = function(modalSelector, tosLinkSelector) {
        $(modalSelector).attr('aria-hidden', 'true');
        $(modalSelector).hide();
        enableTabIndexingOn('.window-wrap');
        $('body').removeClass('open-modal');
        $(modalSelector).find('iframe').remove();
        $(tosLinkSelector).focus();
    };

    var buildModal = function(modalClass, contentClass, closeButtonClass) {
        // Create the modal container
        var modalTitle = gettext('Terms of Service and Honor Code'),
            closeLabel = gettext('Close'),
            titleId = 'modal-header-text',
            $modal = $('<div>', {
                class: modalClass,
                'aria-hidden': 'true'
            }),
            $content = $('<div>', {
                class: contentClass,
                role: 'dialog',
                'aria-modal': 'true',
                'aria-labelledby': titleId
            }),
            $header = $('<div>', {
                class: 'header'
            }),
            $closeButton = $('<button>', {
                'aria-label': closeLabel,
                class: closeButtonClass
            }),
            $title = $('<h1>', {
                id: titleId
            });
        $closeButton.text(closeLabel);
        $title.text(modalTitle);
        $header.append($title);
        $header.append($closeButton);
        $content.append($header);
        $modal.append($content);
        return $modal;
    };

    var buildIframe = function(link, modalSelector, contentSelector, tosLinkSelector) {
        // Create an iframe with contents from the link and set its height to match the content area
        return $('<iframe>', {
            title: 'Terms of Service and Honor Code',
            src: link.href,
            load: function() {
                var $iframeHead = $(this).contents().find('head'),
                    $iframeBody = $(this).contents().find('body');
                // Overwrite styles in child page to hide top navigation and footer
                var $style = $('<style>', {type: 'text/css'}),
                    styleContent = [
                        '/* Default honor.html template */',
                        '.nav-skip, header#global-navigation, .wrapper-footer {',
                        '    display: none;',
                        '}',
                        '.container.about {',
                        '    min-width: auto;',
                        '}',
                        '/* https://www.edx.org/edx-terms-service */',
                        '.edx-header, #skip-link, footer {',
                        '    display: none;',
                        '}',
                        '.region-banner, #breadcrumb + .region-column-wrapper, .edx-header + .region-column-wrapper {',
                        '    margin-top: 0;',
                        '    padding-top: 10px;',
                        '}',
                        'body.node-type-page h1.field-page-tagline {',
                        '    font-size: 16px;',
                        '}',
                        '/* edx-themes */',
                        '.page-heading, .footer-main {',
                        '    display: none;',
                        '}'
                    ].join('\n');
                $style.text(styleContent);
                $iframeHead.append($style);
                // Set the iframe's height to fill the available space
                $(this).css({
                    height: $(contentSelector).height()
                });
                // Hide the modal when ESC is pressed and the iframe is focused
                $iframeBody.keydown(function(event) {
                    if ($(modalSelector).is(':visible') && event.keyCode === 27) {
                        event.preventDefault();
                        hideModal(modalSelector, tosLinkSelector);
                    }
                });
            }
        });
    };

    $(document).ready(function() {
        var tosLinkSelector = '.checkbox-honor_code .supplemental-link a',
            closeButtonClass = 'modal-close-button',
            closeButtonSelector = '.' + closeButtonClass,
            contentClass = 'modal-content',
            contentSelector = '.' + contentClass,
            modalClass = 'tos-modal',
            modalSelector = '.' + modalClass;

        $('body').on('click', tosLinkSelector, function(event) {
            var link = event.target,
                $modal,
                $iframe;
            event.preventDefault();
            // Ignore disabled TOS
            if (link.href.endsWith('#')) {
                return;
            }
            // Add the modal if it doesn't exist yet
            if ($(modalSelector).length < 1) {
                $modal = buildModal(modalClass, contentClass, closeButtonClass);
                $('body').append($modal);
            }
            // Add a new iframe to the content area
            $iframe = buildIframe(link, modalSelector, contentSelector, tosLinkSelector);
            $(contentSelector).append($iframe);
            showModal(modalSelector);
            $(closeButtonSelector).focus();
        });

        $('body').on('click', closeButtonSelector, function() {
            hideModal(modalSelector, tosLinkSelector);
        });

        // Hide the modal when clicking outside its content
        $('body').on('click', modalSelector, function(event) {
            if ($(event.target).hasClass(modalClass)) {
                hideModal(modalSelector, tosLinkSelector);
            }
        });

        // Hide the modal when ESC is pressed and the modal is focused
        $(document).keydown(function(event) {
            if ($(modalSelector).is(':visible') && event.keyCode === 27) {
                event.preventDefault();
                hideModal(modalSelector, tosLinkSelector);
            }
        });
    });
}(jQuery, gettext));
