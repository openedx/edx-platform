var edx = edx || {},

    Dropdown = (function() {

        var _dropdown = {

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

                if (_dropdown.opts.button.length && _dropdown.opts.menu.length) {

                    if (parent) {
                        _dropdown.opts.page = $(parent);
                    }

                    _dropdown.listenForClick();
                    _dropdown.listenForKeypress();
                }
            },

            listenForClick: function() {

                _dropdown.opts.button.on('click', function() {
                    _dropdown.closeDropdownMenu(); // close any open menus
                    _dropdown.openDropdownMenu($(this)); // then open the chosen menu
                });

                _dropdown.opts.page.on('click', function() {
                    _dropdown.closeDropdownMenu();
                });
            },

            listenForKeypress: function() {

                _dropdown.opts.page.on('keydown', function(e) {
                    var keyCode = e.keyCode,
                        focused = $(e.currentTarget.activeElement),
                        items, menu;

                    if (27 === keyCode) {
                        // When the ESC key is pressed, close all menus
                        _dropdown.closeDropdownMenus();
                    }

                    if (focused.is('.action')) {
                        // Key handlers for when a menu item has focus
                        menu = focused.closest('.dropdown-menu');

                        switch (keyCode) {
                            case 38:
                                _dropdown.previousMenuItemLink(focused, menu);
                                break;

                            case 40:
                                _dropdown.nextMenuItemLink(focused, menu);
                                break;

                            case 27:
                                _dropdown.closeDropdownMenus();
                                break;
                        }

                    } else if (focused.is('.has-dropdown')) {
                        // Key handlers for when the button that opens the menu has focus
                        switch(keyCode) {
                            case 40:
                                _dropdown.openDropdownMenu(focused);
                                break;

                            case 13:
                                _dropdown.openDropdownMenu(focused);
                                break;

                            case 27:
                                _dropdown.closeDropdownMenus();
                                break;
                        }
                    } else if (focused.is('.dropdown-menu')) {
                        // Key handlers for when the menu itself has focus, before an item within it receives focus
                        menu = focused.closest('.dropdown-menu');

                        switch(keyCode) {
                            case 40:
                                _dropdown.focusFirstItem(menu);
                                break;

                            case 27:
                                _dropdown.closeDropdownMenus();
                                break;
                        }
                    } else {

                        switch(keyCode) {
                            case 13:
                            case 38:
                            case 40:
                            case 27:
                        }
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

            closeDropdownMenu: function() {
                var open = _dropdown.opts.page.find(_dropdown.opts.menu).not(':focus');

                if (open) {
                    open
                        .removeClass(_dropdown.opts.menu_active)
                        .addClass(_dropdown.opts.menu_inactive);

                    open.parent()
                        .find(_dropdown.opts.button)
                        .removeClass(_dropdown.opts.button_active)
                        .attr('aria-expanded', 'false');
                }
            },

            closeDropdownMenus: function() {
                var open = _dropdown.opts.page.find(_dropdown.opts.menu);

                if (open) {
                    open
                        .removeClass(_dropdown.opts.menu_active)
                        .addClass(_dropdown.opts.menu_inactive);

                    open.parent()
                        .find(_dropdown.opts.button)
                        .removeClass(_dropdown.opts.button_active)
                        .attr('aria-expanded', 'false');
                }
            },

            openDropdownMenu: function(el) {
                var menu = el.parent().find(_dropdown.opts.menu);

                if (menu.hasClass(_dropdown.opts.menu_active)) {
                    return false;
                } else {
                    el.addClass(_dropdown.opts.button_active)
                        .attr('aria-expanded', 'true');

                    menu
                        .removeClass(_dropdown.opts.menu_inactive)
                        .addClass(_dropdown.opts.menu_active);

                    _dropdown.setFocus(menu);
                    _dropdown.setOrientation(el);
                }
            },

            setFocus: function(menu) {
                var first = menu.children('.dropdown-item').first().find('.action');

                menu
                    .focus();
            },

            setOrientation: function(el) {

                el.parent().find(_dropdown.opts.menu)
                    .removeClass(_dropdown.opts.menu_align + 'left')
                    .removeClass(_dropdown.opts.menu_align + 'right');

                if (el.offset().left > _dropdown.opts.midpoint) {
                    el.parent().find(_dropdown.opts.menu)
                        .addClass(_dropdown.opts.menu_align + 'right');
                } else {
                    el.parent().find(_dropdown.opts.menu)
                        .addClass(_dropdown.opts.menu_align + 'left');
                }
            }

        };

        return {
            init: _dropdown.init
        };

    })();

    edx.util = edx.util || {};
    edx.util.dropdown = Dropdown;
    edx.util.dropdown.init();
