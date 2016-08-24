$(document).ready(function() {
    'use strict';

  // define variables for code legibility
    var dropdownMenuToggle = $('.dropdown');
    var dropdownMenu = $('.dropdown-menu');
    var menuItems = dropdownMenu.find('a');

  // bind menu toggle click for later use
    dropdownMenuToggle.toggle(function() {
        dropdownMenu.addClass('expanded').find('a').first().focus();
        dropdownMenuToggle.addClass('active').attr('aria-expanded', 'true');
    }, function() {
        dropdownMenu.removeClass('expanded');
        dropdownMenuToggle.removeClass('active').attr('aria-expanded', 'false').focus();
    });

  // catch keypresses when focused on dropdownMenuToggle (we only care about spacebar keypresses here)
    dropdownMenuToggle.on('keydown', function(event) {
    // if space key pressed
        if (event.which == 32) {
            dropdownMenuToggle.click();
            event.preventDefault();
        }
    });

  // catch keypresses when inside dropdownMenu (we want to catch spacebar; escape; up arrow or shift+tab; and down arrow or tab)
    dropdownMenu.on('keydown', function(event) {
        catchKeyPress($(this), event);
    });

    function catchKeyPress(object, event) {
    // get currently focused item
        var focusedItem = jQuery(':focus');

    // get the number of focusable items
        var numberOfMenuItems = menuItems.length;

    // get the index of the currently focused item
        var focusedItemIndex = menuItems.index(focusedItem);

    // var to store next focused item index
        var itemToFocusIndex;

    // if space key pressed
        if (event.which == 32) {
            dropdownMenuToggle.click();
            event.preventDefault();
        }

    // if escape key pressed
        if (event.which == 27) {
            dropdownMenuToggle.click();
            event.preventDefault();
        }

        // if up arrow key pressed or shift+tab else down key or tab is pressed
        if (event.which == 38 || (event.which == 9 && event.shiftKey)) {
            // if first item go to last
            if (focusedItemIndex === 0) {
                menuItems.last().focus();
            } else {
                itemToFocusIndex = focusedItemIndex - 1;
                menuItems.get(itemToFocusIndex).focus();
            }
            event.preventDefault();
        } else if (event.which == 40 || event.which == 9) {
            // if last item go to first
            if (focusedItemIndex == numberOfMenuItems - 1) {
                menuItems.first().focus();
            } else {
                itemToFocusIndex = focusedItemIndex + 1;
                menuItems.get(itemToFocusIndex).focus();
            }
            event.preventDefault();
        }
    }
});
