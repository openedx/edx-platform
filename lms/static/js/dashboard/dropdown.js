var edx = edx || {};

(function ($) {
    'use strict';

    edx.dashboard = edx.dashboard || {};
    edx.dashboard.dropdown = {};

    // Generate the properties object to be passed along with business intelligence events.
    edx.dashboard.dropdown.toggleCourseActionsDropdownMenu = function (event) {
        // define variables for code legibility
        var dashboardIndex = $(event.currentTarget).data().dashboardIndex,
            dropdown = $('#actions-dropdown-' + dashboardIndex),
            dropdownButton = $('#actions-dropdown-link-' + dashboardIndex),
            ariaExpandedState = (dropdownButton.attr('aria-expanded') === 'true'),
            menuItems = dropdown.find('a');

        var catchKeyPress = function(object, event) {
            // get currently focused item
            var focusedItem = $(':focus');

            // get the index of the currently focused item
            var focusedItemIndex = menuItems.index(focusedItem);

            // var to store next focused item index
            var itemToFocusIndex;

            // if space or escape key pressed
            if ( event.which === 32 || event.which === 27) {
              dropdownButton.click();
              event.preventDefault();
            }

            // if up arrow key pressed or shift+tab
            else if (event.which === 38 || (event.which === 9 && event.shiftKey)) {
              // if first item go to last
              if (focusedItemIndex === 0 || focusedItemIndex === -1) {
                menuItems.last().focus();
              } else {
                itemToFocusIndex = focusedItemIndex - 1;
                menuItems.get(itemToFocusIndex).focus();
              }
              event.preventDefault();
            }

            // if down arrow key pressed or tab key
            else if (event.which === 40 || event.which === 9) {
              // if last item go to first
              if (focusedItemIndex === menuItems.length - 1 || focusedItemIndex === -1) {
                menuItems.first().focus();
              } else {
                itemToFocusIndex = focusedItemIndex + 1;
                menuItems.get(itemToFocusIndex).focus();
              }
              event.preventDefault();
            }
        };

        // Toggle the visibility control for the selected element and set the focus
        dropdown.toggleClass('is-visible');
        if (dropdown.hasClass('is-visible')) {
            dropdown.attr('tabindex', -1);
            dropdown.focus();
        } else {
            dropdown.removeAttr('tabindex');
            dropdownButton.focus();
        }

        // Inform the ARIA framework that the dropdown has been expanded
        dropdownButton.attr('aria-expanded', !ariaExpandedState);

        //catch keypresses when inside dropdownMenu (we want to catch spacebar;
        // escape; up arrow or shift+tab; and down arrow or tab)
        dropdown.on('keydown', function(event){
          catchKeyPress($(this), event);
        });
    };

    edx.dashboard.dropdown.bindToggleButtons = function() {
      $('.action-more').bind(
        'click',
        edx.dashboard.dropdown.toggleCourseActionsDropdownMenu
      );
    };

    $(document).ready(function() {
      edx.dashboard.dropdown.bindToggleButtons();
    });

})(jQuery);
