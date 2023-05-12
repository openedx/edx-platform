/* eslint-disable-next-line no-shadow-restricted-names, no-unused-vars */
(function(undefined) {
    'use strict';

    // [module Collapsible]
    //
    // [description]
    //     Set of library functions that provide a simple way to add
    //     collapsible functionality to elements.
    this.Collapsible = {
        // eslint-disable-next-line no-use-before-define
        setCollapsibles: setCollapsibles,
        // eslint-disable-next-line no-use-before-define
        toggleFull: toggleFull,
        // eslint-disable-next-line no-use-before-define
        toggleHint: toggleHint
    };

    // eslint-disable-next-line no-useless-return
    return;

    // [function setCollapsibles]
    //
    // [description]
    //     Scan element's content for generic collapsible containers.
    //
    // [params]
    //     el: container
    function setCollapsibles(el) {
        /* eslint-disable-next-line camelcase, no-var */
        var linkBottom, linkTop, short_custom;

        linkTop = '<a href="#" class="full full-top">See full output</a>';
        linkBottom = '<a href="#" class="full full-bottom">See full output</a>';

        // Standard longform + shortfom pattern.
        el.find('.longform').hide();
        el.find('.shortform').append(linkTop, linkBottom); // xss-lint: disable=javascript-jquery-append

        // Custom longform + shortform text pattern.
        // eslint-disable-next-line camelcase
        short_custom = el.find('.shortform-custom');

        // Set up each one individually.
        // eslint-disable-next-line camelcase
        short_custom.each(function(index, elt) {
            /* eslint-disable-next-line camelcase, no-var */
            var close_text, open_text;

            // eslint-disable-next-line camelcase
            open_text = $(elt).data('open-text');
            // eslint-disable-next-line camelcase
            close_text = $(elt).data('close-text');
            edx.HtmlUtils.append(
                $(elt),
                edx.HtmlUtils.joinHtml(
                    edx.HtmlUtils.HTML("<a href='#' class='full-custom'>"),
                    gettext(open_text),
                    edx.HtmlUtils.HTML('</a>')
                )
            );

            $(elt).find('.full-custom').click(function(event) {
                // eslint-disable-next-line no-undef
                Collapsible.toggleFull(event, open_text, close_text);
            });
        });

        // Collapsible pattern.
        el.find('.collapsible header + section').hide();

        // Set up triggers.
        el.find('.full').click(function(event) {
            // eslint-disable-next-line no-undef
            Collapsible.toggleFull(event, 'See full output', 'Hide output');
        });
        // eslint-disable-next-line no-undef
        el.find('.collapsible header a').click(Collapsible.toggleHint);
    }

    // [function toggleFull]
    //
    // [description]
    //     Toggle the display of full text for a collapsible element.
    //
    // [params]
    //     event: jQuery event object associated with the event that
    //         triggered this callback function.
    //     open_text: text that should be displayed when the collapsible
    //         is open.
    //     close_text: text that should be displayed when the collapsible
    //         is closed.
    // eslint-disable-next-line camelcase
    function toggleFull(event, open_text, close_text) {
        /* eslint-disable-next-line camelcase, no-var */
        var $el, new_text, parent;

        event.preventDefault();

        parent = $(event.target).parent();
        parent.siblings().slideToggle();
        parent.parent().toggleClass('open');

        // eslint-disable-next-line camelcase
        if ($(event.target).text() === open_text) {
            // eslint-disable-next-line camelcase
            new_text = close_text;
        } else {
            // eslint-disable-next-line camelcase
            new_text = open_text;
        }

        if ($(event.target).hasClass('full')) {
            $el = parent.find('.full');
        } else {
            $el = $(event.target);
        }

        $el.text(new_text);
    }

    // [function toggleHint]
    //
    // [description]
    //     Toggle the collapsible open to show the hint.
    //
    // [params]
    //     event: jQuery event object associated with the event that
    //         triggered this callback function.
    function toggleHint(event) {
        event.preventDefault();

        $(event.target).parent().siblings().slideToggle();
        $(event.target).parent().parent().toggleClass('open');
    }
}).call(this);
