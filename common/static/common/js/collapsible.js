(function() {
    'use strict';
    // [module Collapsible]
    //
    // [description]
    //     Set of library functions that provide a simple way to add
    //     collapsible functionality to elements.

    var Collapsible = {};

    // [function setCollapsibles]
    //
    // [description]
    //     Scan element's content for generic collapsible containers.
    //
    // [params]
    //     el: container
    function setCollapsibles(el) {
        var linkBottom, linkTop, shortCustom;

        linkTop = '<a href="#" class="full full-top">See full output</a>';
        linkBottom = '<a href="#" class="full full-bottom">See full output</a>';

        // Standard longform + shortfom pattern.
        el.find('.longform').hide();
        edx.HtmlUtils.append(el.find('.shortform'), edx.StringUtils.interpolate(
                '{linkTop}{linkBottom}', {
                linkTop: linkTop,
                linkBottom: linkBottom
            })
        );

        // Custom longform + shortform text pattern.
        shortCustom = el.find('.shortform-custom');

        // Set up each one individually.
        shortCustom.each(function(index, elt) {
            var closeText, openText;

            openText = $(elt).data('open-text');
            closeText = $(elt).data('close-text');
            edx.HtmlUtils.append($(elt), edx.StringUtils.interpolate(
                    "<a href='#' class='full-custom'>{text}</a>", {
                    text: openText
                })
            );

            $(elt).find('.full-custom').click(function(event) {
                Collapsible.toggleFull(event, openText, closeText);
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
    //     openText: text that should be displayed when the collapsible
    //         is open.
    //     closeText: text that should be displayed when the collapsible
    //         is closed.
    function toggleFull(event, openText, closeText) {
        var $el, newText, parent;

        event.preventDefault();

        parent = $(event.target).parent();
        parent.siblings().slideToggle();
        parent.parent().toggleClass('open');

        if ($(event.target).text() === openText) {
            newText = closeText;
        } else {
            newText = openText;
        }

        if ($(event.target).hasClass('full')) {
            $el = parent.find('.full');
        } else {
            $el = $(event.target);
        }

        $el.text(newText);
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

        $(event.target).parent().siblings()
            .slideToggle();
        $(event.target).parent().parent()
            .toggleClass('open');
    }

    Collapsible.setCollapsibles = setCollapsibles;
    Collapsible.toggleFull = toggleFull;
    Collapsible.toggleHint = toggleHint;

    this.Collapsible = Collapsible;
    return;

}).call(this);
