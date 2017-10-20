/**
 * Ensuring collapsible and accessible components on multiple
 * screen sizes for the responsive lms header.
*/

function createMobileMenu() {
    /**
     * Dynamically create a mobile menu from all specified mobile links
     * on the page.
     */
    'use strict';
    $('.mobile-nav-item').each(function() {
        var mobileNavItem = $(this).clone().addClass('mobile-nav-link');
        mobileNavItem.attr('role', 'menuitem');
        // xss-lint: disable=javascript-jquery-append
        $('.mobile-menu').append(mobileNavItem);
    });
}

$(document).ready(function() {
    'use strict';
    var $hamburgerMenu;
    var $mobileMenu;
    // Toggling visibility for the user dropdown
    $('.toggle-user-dropdown').click(function() {
        var $dropdownMenu = $('.global-header .nav-item .dropdown-user-menu');
        var $userMenu = $('.user-dropdown');
        if ($dropdownMenu.is(':visible')) {
            $dropdownMenu.hide();
            $userMenu.attr('aria-expanded', 'false');
        } else {
            $dropdownMenu.show();
            $dropdownMenu.find('.dropdown-item')[0].focus();
            $userMenu.attr('aria-expanded', 'true');
        }
        $('.toggle-user-dropdown').toggleClass('open');
    });

    // Toggling menu visibility with the hamburger menu
    $('.hamburger-menu').click(function() {
        $hamburgerMenu = $('.hamburger-menu');
        $mobileMenu = $('.mobile-menu');
        if ($mobileMenu.is(':visible')) {
            $mobileMenu.hide();
            $hamburgerMenu.attr('aria-expanded', 'false');
        } else {
            $mobileMenu.show();
            $hamburgerMenu.attr('aria-expanded', 'true');
        }
        $hamburgerMenu.toggleClass('open');
    });

    // Hide hamburger menu if no nav items (sign in and register pages)
    if ($('.mobile-nav-item').size() === 0) {
        $('.hamburger-menu').css('display', 'none');
    }

    createMobileMenu();
});

// Ensure click away hides the user dropdown
$(window).click(function(e) {
    'use strict';
    if (!$(e.target).is('.dropdown-item, .toggle-user-dropdown')) {
        $('.global-header .nav-item .dropdown-user-menu').hide();
    }
});

// Accessibility keyboard controls for user dropdown and mobile menu
$(document).on('keydown', function(e) {
    'use strict';
    var isNext;
    var nextLink;
    var loopFirst;
    var loopLast;
    var isLastItem = $(e.target).parent().is(':last-child');
    var isToggle = $(e.target).hasClass('toggle-user-dropdown');
    var isHamburgerMenu = $(e.target).hasClass('hamburger-menu');
    var isMobileOption = $(e.target).parent().hasClass('mobile-nav-link');
    var isDropdownOption = !isMobileOption && $(e.target).parent().hasClass('dropdown-item');
    var $userMenu = $('.user-dropdown');
    var $hamburgerMenu = $('.hamburger-menu');
    var $toggleUserDropdown = $('.toggle-user-dropdown');

    // Open or close relevant menu on enter or space click and focus on first element.
    if ((e.keyCode === 13 || e.keyCode === 32) && (isToggle || isHamburgerMenu)) {
        $(e.target).click();
        if (isHamburgerMenu) {
            if ($('.mobile-menu').is(':visible')) {
                $hamburgerMenu.attr('aria-expanded', true);
                $('.mobile-menu .mobile-nav-link a').first().focus();
            } else {
                $hamburgerMenu.attr('aria-expanded', false);
            }
        } else if (isToggle) {
            if ($('.global-header .nav-item .dropdown-user-menu').is(':visible')) {
                $userMenu.attr('aria-expanded', 'true');
                $('.dropdown-item a:first').focus();
            } else {
                $userMenu.attr('aria-expanded', false);
            }
        }
        // Don't allow for double click or page jump on Firefox browser
        e.preventDefault();
        e.stopPropagation();
    }

    // Enable arrow functionality within the menu.
    if (e.keyCode === 38 || e.keyCode === 40 && (isDropdownOption || isMobileOption ||
        (isHamburgerMenu && $hamburgerMenu.hasClass('open')) || isToggle && $toggleUserDropdown.hasClass('open'))) {
        isNext = e.keyCode === 40;
        if (isNext && !isHamburgerMenu && !isToggle && isLastItem) {
            // Loop to the start from the final element
            nextLink = isDropdownOption ? $toggleUserDropdown : $hamburgerMenu;
        } else if (!isNext && (isHamburgerMenu || isToggle)) {
            // Loop to the end when up arrow pressed from menu icon
            nextLink = isHamburgerMenu ? $('.mobile-menu .mobile-nav-link a').last()
                : $('.dropdown-user-menu .dropdown-nav-item').last().find('a');
        } else if (isNext && (isHamburgerMenu || isToggle)) {
            // Loop to the first element from the menu icon
            nextLink = isHamburgerMenu ? $('.mobile-menu .mobile-nav-link a').first()
                : $('.dropdown-user-menu .dropdown-nav-item').first().find('a');
        } else {
            // Loop up to the menu icon if first element in menu
            if (!isNext && $(e.target).parent().is(':first-child') && !isHamburgerMenu && !isToggle) {
                nextLink = isDropdownOption ? $toggleUserDropdown : $hamburgerMenu;
            } else {
                nextLink = isNext ?
                    $(e.target).parent().next().find('a') : // eslint-disable-line newline-per-chained-call
                    $(e.target).parent().prev().find('a'); // eslint-disable-line newline-per-chained-call
            }
        }
        nextLink.focus();

        // Don't let the screen scroll on navigation
        e.preventDefault();
        e.stopPropagation();
    }

    // Escape clears out of the menu
    if (e.keyCode === 27 && (isDropdownOption || isHamburgerMenu || isMobileOption || isToggle)) {
        if (isDropdownOption || isToggle) {
            $('.global-header .nav-item .dropdown-user-menu').hide();
            $toggleUserDropdown.focus();
            $userMenu.attr('aria-expanded', 'false');
            $('.toggle-user-dropdown').removeClass('open');
        } else {
            $('.mobile-menu').hide();
            $hamburgerMenu.focus();
            $hamburgerMenu.attr('aria-expanded', 'false');
            $hamburgerMenu.removeClass('open');
        }
    }

    // Loop when tabbing and using arrows
    if ((e.keyCode === 9) && ((isDropdownOption && isLastItem) || (isMobileOption && isLastItem) || (isHamburgerMenu
        && $hamburgerMenu.hasClass('open')) || (isToggle && $toggleUserDropdown.hasClass('open')))) {
        nextLink = null;
        loopFirst = isLastItem && !e.shiftKey && !isHamburgerMenu && !isToggle;
        loopLast = (isHamburgerMenu || isToggle) && e.shiftKey;
        if (!(loopFirst || loopLast)) {
            return;
        }
        if (isDropdownOption || isToggle) {
            nextLink = loopFirst ? $toggleUserDropdown : $('.dropdown-user-menu .dropdown-nav-item a').last();
        } else {
            nextLink = loopFirst ? $hamburgerMenu : $('.mobile-menu .mobile-nav-link a').last();
        }
        nextLink.focus();
        e.preventDefault();
    }
});
