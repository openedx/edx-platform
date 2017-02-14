(function(undefined) {
    'use strict';

    // [module Collapsible]
    //
    // [description]
    //     Set of library functions that provide a simple way to add
    //     collapsible functionality to elements.
    this.Collapsible = {
        setCollapsibles: setCollapsibles,
        toggleFull: toggleFull,
        toggleHint: toggleHint
    };

    return;

    // [function setCollapsibles]
    //
    // [description]
    //     Scan element's content for generic collapsible containers.
    //
    // [params]
    //     el: container
    function setCollapsibles(el) {
        var linkBottom, linkTop, short_custom;

        linkTop = '<a href="#" class="full full-top">See full output</a>';
        linkBottom = '<a href="#" class="full full-bottom">See full output</a>';

        // Standard longform + shortfom pattern.
        el.find('.longform').hide();
        el.find('.shortform').append(linkTop, linkBottom);

        // Custom longform + shortform text pattern.
        short_custom = el.find('.shortform-custom');

        // Set up each one individually.
        short_custom.each(function(index, elt) {
            var close_text, open_text;

            open_text = $(elt).data('open-text');
            close_text = $(elt).data('close-text');
            $(elt).append("<a href='#' class='full-custom'>" + open_text + '</a>');

            $(elt).find('.full-custom').click(function(event) {
                Collapsible.toggleFull(event, open_text, close_text);
            });
        });

        // Collapsible pattern.
        el.find('.collapsible header + section').hide();

        // Set up triggers.
        el.find('.full').click(function(event) {
            Collapsible.toggleFull(event, 'See full output', 'Hide output');
        });
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
    function toggleFull(event, open_text, close_text) {
        var el, new_text, parent;

        event.preventDefault();

        parent = $(event.target).parent();
        parent.siblings().slideToggle();
        parent.parent().toggleClass('open');

        if ($(event.target).text() === open_text) {
            new_text = close_text;
        } else {
            new_text = open_text;
        }

        if ($(event.target).hasClass('full')) {
            el = parent.find('.full');
        } else {
            el = $(event.target);
        }

        el.text(new_text);
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
