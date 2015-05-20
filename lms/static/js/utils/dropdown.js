var edx = edx || {},

    Dropdown = (function() {

        var dropdown = {

            opts: {
                page: $(document),
                midpoint: ($(window).width() / 2),
                button: $('.button-more.has-dropdown'),
                button_active: 'is-active',
                menu: $('.dropdown-menu'),
                menu_inactive: 'is-hidden',
                menu_active: 'is-visible',
                menu_align: 'align-',
                text_align: 'control-text-align'
            },

            init: function(parent) {

                if (dropdown.opts.button.length && dropdown.opts.menu.length) {

                    if (parent) {
                        dropdown.opts.page = $(parent);
                    }

                    dropdown.listenForClick();
                    dropdown.listenForKeypress();
                }
            },

            listenForClick: function() {

                dropdown.opts.button.on('click', function() {
                    dropdown.closeDropdownMenus(); // close any open menus
                    dropdown.openDropdownMenu($(this)); // then open the chosen menu
                });

                dropdown.opts.page.on('click', function() {
                    dropdown.closeDropdownMenus();
                });
            },

            handlerIsAction: function(key, menu) {
                if (key === 38) { // UP
                    dropdown.previousMenuItemLink(focused, menu);
                } else if (key === 40) { // DOWN
                    dropdown.nextMenuItemLink(focused, menu);
                } else if (key === 27) { // ESC
                    dropdown.closeDropdownMenus();
                }
            },

            handlerIsButton: function(key, el) {
                if (key === 40 || key === 13) { // DOWN or ENTER
                    dropdown.openDropdownMenu(el);
                }
            },

            handlerIsMenu: function(key, menu) {
                if (key === 40) { // DOWN
                    dropdown.focusFirstItem(menu);
                }
            },

            listenForKeypress: function() {

                dropdown.opts.page.on('keydown', function(e) {
                    var keyCode = e.keyCode,
                        focused = $(e.currentTarget.activeElement),
                        items, menu;

                    if (27 === keyCode) {
                        // When the ESC key is pressed, close all menus
                        dropdown.closeDropdownMenus(true);
                    }

                    if (focused.is('.action')) {
                        // Key handlers for when a menu item has focus
                        menu = focused.closest('.dropdown-menu');
                        dropdown.handlerIsAction(keyCode, menu);

                    } else if (focused.is('.has-dropdown')) {
                        // Key handlers for when the button that opens the menu has focus
                        dropdown.handlerIsButton(keyCode, focused);

                    } else if (focused.is('.dropdown-menu')) {
                        // Key handlers for when the menu itself has focus, before an item within it receives focus
                        menu = focused.closest('.dropdown-menu');
                        dropdown.handlerIsMenu(keyCode, menu);
                    }
                });
            },

            previousMenuItemLink: function(focused, menu) {
                var items = menu.children('.dropdown-item').find('.action'),
                    index = items.index(focused),
                    prev = index - 1;

                if (index === 0) {
                    items.last().focus();
                } else {
                    items.eq(prev).focus();
                }
            },

            nextMenuItemLink: function(focused, menu) {
                var items = menu.children('.dropdown-item').find('.action'),
                    items_count = items.length -1,
                    index = items.index(focused),
                    next = index + 1;

                if (index === items_count) {
                    items.first().focus();
                } else {
                    items.eq(next).focus();
                }
            },

            focusFirstItem: function(menu) {
                menu.find('.dropdown-item:first .action').focus();
            },

            closeDropdownMenus: function(all) {
                if (all) {
                    // Close all open, usually from ESC or doc click
                    var open = dropdown.opts.page.find(dropdown.opts.menu);
                } else {
                    // Closing one for another
                    var open = dropdown.opts.page.find(dropdown.opts.menu).not(':focus');
                }

                open.removeClass(dropdown.opts.menu_active)
                    .addClass(dropdown.opts.menu_inactive);

                open.parent()
                    .find(dropdown.opts.button)
                    .removeClass(dropdown.opts.button_active)
                    .attr('aria-expanded', 'false');
            },

            openDropdownMenu: function(el) {
                var menu = el.parent().find(dropdown.opts.menu);

                if (!menu.hasClass(dropdown.opts.menu_active)) {
                    el.addClass(dropdown.opts.button_active)
                        .attr('aria-expanded', 'true');

                    menu.removeClass(dropdown.opts.menu_inactive)
                        .addClass(dropdown.opts.menu_active);

                    dropdown.setFocus(menu);
                    dropdown.setOrientation(el);
                }
            },

            setFocus: function(menu) {
                var first = menu.children('.dropdown-item').first().find('.action');

                menu.focus();
            },

            setOrientation: function(el) {

                el.parent()
                    .find(dropdown.opts.menu)
                    .removeClass(dropdown.opts.menu_align + 'left')
                    .removeClass(dropdown.opts.menu_align + 'right');

                if (el.offset().left > dropdown.opts.midpoint) {
                    el.parent()
                        .find(dropdown.opts.menu)
                        .addClass(dropdown.opts.menu_align + 'right');
                } else {
                    el.parent()
                        .find(dropdown.opts.menu)
                        .addClass(dropdown.opts.menu_align + 'left');
                }
            }

        };

        return {
            init: dropdown.init
        };

    })();

    edx.util = edx.util || {};
    edx.util.dropdown = Dropdown;
    edx.util.dropdown.init();
