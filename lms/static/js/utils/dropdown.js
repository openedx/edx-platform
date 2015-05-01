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

                that.opts.page.keyup(function(e) {
                    if (27 === e.which) {
                        that.closeDropdownMenus();
                    }
                });
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
                var that = _dropdown;

                if (el.parent().find(that.opts.menu).hasClass(that.opts.menu_active)) {
                    return false;
                } else {
                    el.parent()
                        .find(that.opts.menu)
                            .removeClass(that.opts.menu_inactive)
                            .addClass(that.opts.menu_active)
                                .focus();

                    el.addClass(that.opts.button_active)
                        .attr('aria-expanded', 'true');

                    that.setOrientation(el);
                }
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
