var edx = edx || {},

    Dropdown = (function() {

        var _dropdown = {

            opts: {
                page: $(document),
                midpoint: ($(window).width() / 2),
                button: $('.button-more.has-dropdown'),
                button_active: 'is-active',
                menu: $('.dropdown'),
                menu_inactive: 'is-hidden',
                menu_active: 'is-visible',
                menu_align: 'align-',
                text_align: 'control-text-align'
            },

            init: function(parent) {
                var that = _dropdown;

                if (parent) {
                    that.opts.page = $(parent);
                }

                _dropdown.listenForClick();
                _dropdown.listenForKeypress();
            },

            listenForClick: function() {
                var that = _dropdown;

                that.opts.button.on('click', function() {
                    that.closeDropdownMenu();
                    that.openDropdownMenu($(this));
                });

                that.opts.page.on('click', function() {
                    that.closeDropdownMenu();
                });
            },

            listenForKeypress: function() {
                var that = _dropdown;

                that.opts.page.on('keydown', function(e) {
                    var keyCode = e.keyCode,
                        focused = $(e.currentTarget.activeElement),
                        items, menu;

                    if (27 === keyCode) {
                        that.closeDropdownMenus();
                    }

                    if (focused.is('.action')) {

                        menu = focused.parent().parent();
                        items = menu.find('.dropdown-item .action').length;

                        switch (keyCode) {
                            case 38:
                                that.previousMenuItemLink(focused, menu);
                                return false;
                                break;

                            case 40:
                                that.nextMenuItemLink(focused, menu);
                                return false;
                                break;

                            case 27:
                                that.closeDropdownMenus();
                                break;
                        }

                    } else if(focused.is('.has-dropdown')) {

                        switch(keyCode) {
                            case 40:
                                that.openDropdownMenu(focused);
                                return false;
                                break;

                            case 13:
                                that.openDropdownMenu(focused);
                                break;

                            case 27:
                                that.closeDropdownMenus();
                                break;
                        }
                    } else if (focused.is('.dropdown')) {

                        menu = focused.parent().parent();

                        switch(keyCode) {
                            case 40:
                                that.focusFirstItem(menu);
                                return false;
                                break;

                            case 27:
                                that.closeDropdownMenus();
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
                    items_count = items.length - 1,
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
                var that = _dropdown;
                    open = that.opts.page.find(that.opts.menu).not(':focus');

                if (open) {
                    open
                        .removeClass(that.opts.menu_active)
                        .addClass(that.opts.menu_inactive);

                    open.parent()
                        .find(that.opts.button)
                        .removeClass(that.opts.button_active)
                        .attr('aria-expanded', 'false');
                }
            },

            closeDropdownMenus: function() {
                var that = _dropdown;
                    open = that.opts.page.find(that.opts.menu);

                if (open) {
                    open
                        .removeClass(that.opts.menu_active)
                        .addClass(that.opts.menu_inactive);

                    open.parent()
                        .find(that.opts.button)
                        .removeClass(that.opts.button_active)
                        .attr('aria-expanded', 'false');
                }
            },

            openDropdownMenu: function(el) {
                var that = _dropdown,
                    menu = el.parent().find(that.opts.menu);

                if (menu.hasClass(that.opts.menu_active)) {
                    return false;
                } else {
                    el.addClass(that.opts.button_active)
                        .attr('aria-expanded', 'true');

                    menu
                        .removeClass(that.opts.menu_inactive)
                        .addClass(that.opts.menu_active);

                    that.setFocus(menu);
                    that.setOrientation(el);
                }
            },

            setFocus: function(menu) {
                var first = menu.children('.dropdown-item').first().find('.action');

                menu
                    .focus();
            },

            setOrientation: function(el) {
                var that = _dropdown;

                el.parent().find(that.opts.menu)
                    .removeClass(that.opts.menu_align + 'left')
                    .removeClass(that.opts.menu_align + 'right');

                if (el.offset().left > that.opts.midpoint) {
                    el.parent().find(that.opts.menu)
                        .addClass(that.opts.menu_align + 'right');
                } else {
                    el.parent().find(that.opts.menu)
                        .addClass(that.opts.menu_align + 'left');
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
