(function (requirejs, require, define) {

// VideoAccessibleMenu module.
define(
'video/035_video_accessible_menu.js',
[],
function () {

    // VideoAccessibleMenu() function - what this module "exports".
    return function (state) {
        var dfd = $.Deferred();

        if (state.el.find('li.video-tracks') === 0) {
            dfd.resolve();
            return dfd.promise();
        }

        state.videoAccessibleMenu = {
            value: state.storage.getItem('transcript_download_format')
        };

        _initialize(state);
        dfd.resolve();
        return dfd.promise();
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    function _initialize(state) {
        _makeFunctionsPublic(state);
        _renderElements(state);
        _addAriaAttributes(state);
        _bindHandlers(state);
    }

    // function _makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called,
    //     these functions will get the 'state' object as a context.
    function _makeFunctionsPublic(state) {
        var methodsDict = {
            changeFileType: changeFileType,
            setValue: setValue
        };

        state.bindTo(methodsDict, state.videoAccessibleMenu, state);
    }

    // function _renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their
    //     initial configuration. Also make the created DOM elements available
    //     via the 'state' object. Much easier to work this way - you don't
    //     have to do repeated jQuery element selects.
    function _renderElements(state) {

        // For the  time being, we assume that the menu structure is present in
        // the template HTML. In the future accessible menu plugin, everything
        // inside <div class='menu-container'></div> will be generated in this
        // file.
        var container = state.el.find('li.video-tracks>div.a11y-menu-container'),
            button = container.children('a.a11y-menu-button'),
            menuList = container.children('ol.a11y-menu-list'),
            menuItems = menuList.children('li.a11y-menu-item'),
            menuItemsLinks = menuItems.children('a.a11y-menu-item-link'),
            value = (function (val, activeElement) {
                return val || activeElement.find('a').data('value') || 'srt';
            }(state.videoAccessibleMenu.value, menuItems.filter('.active'))),
            msg = '.' + value;

        $.extend(state.videoAccessibleMenu, {
            container: container,
            button: button,
            menuList: menuList,
            menuItems: menuItems,
            menuItemsLinks: menuItemsLinks
        });

        if (value) {
            state.videoAccessibleMenu.setValue(value);
            button.text(gettext(msg));
        }
    }

    function _addAriaAttributes(state) {
        var menu = state.videoAccessibleMenu;

        menu.button.attr({
            'role': 'button',
            'aria-disabled': 'false'
        });

        menu.menuList.attr('role', 'menu');

        menu.menuItemsLinks.each(function(){
            $(this).attr({
                'role': 'menuitem',
                'aria-disabled': 'false'
            });
        });
    }

    // Get previous element in array or cyles back to the last if it is the
    // first.
    function _previousMenuItemLink(links, index) {
        return $(links.eq(index < 1 ? links.length - 1 : index - 1));
    }

    // Get next element in array or cyles back to the first if it is the last.
    function _nextMenuItemLink(links, index) {
        return $(links.eq(index >= links.length - 1 ? 0 : index + 1));
    }

    function _menuItemsLinksFocused(menu) {
        return menu.menuItemsLinks.is(':focus');
    }

    function _openMenu(menu, without_handler) {
        // When menu items have focus, the menu stays open on
        // mouseleave. A _closeMenuHandler is added to the window
        // element to have clicks close the menu when they happen
        // outside of it. We namespace the click event to easily remove it (and
        // only it) in _closeMenu.
        menu.container.addClass('open');
        menu.button.text('...');
        if (!without_handler) {
            $(window).on('click.currentMenu', _closeMenuHandler.bind(menu));
        }

        // @TODO: onOpen callback
    }

    function _closeMenu(menu, without_handler) {
        // Remove the previously added clickHandler from window element.
        var msg = '.' + menu.value;

        menu.container.removeClass('open');
        menu.button.text(gettext(msg));
        if (!without_handler) {
            $(window).off('click.currentMenu');
        }

        // @TODO: onClose callback
    }

    function _openMenuHandler(event) {
        _openMenu(this, true);

        return false;
    }

    function _closeMenuHandler(event) {
        // Only close the menu if no menu item link has focus or `click` event.
        if (!_menuItemsLinksFocused(this) || event.type == 'click') {
            _closeMenu(this, true);
        }

        return false;
    }

    function _toggleMenuHandler(event) {
        if (this.container.hasClass('open')) {
            _closeMenu(this, true);
        } else {
            _openMenu(this, true);
        }

        return false;
    }

    // Various event handlers. They all return false to stop propagation and
    // prevent default behavior.
    function _clickHandler(event) {
        var target = $(event.currentTarget);

        this.changeFileType.call(this, event);
        _closeMenu(this, true);

        return false;
    }

    function _keyDownHandler(event) {
        var KEY = $.ui.keyCode,
            keyCode = event.keyCode,
            target = $(event.currentTarget),
            index;

        if (target.is('a.a11y-menu-item-link')) {

            index = target.parent().index();

            switch (keyCode) {
                // Scroll up menu, wrapping at the top. Keep menu open.
                case KEY.UP:
                    _previousMenuItemLink(this.menuItemsLinks, index).focus();
                    break;
                // Scroll down  menu, wrapping at the bottom. Keep menu
                // open.
                case KEY.DOWN:
                    _nextMenuItemLink(this.menuItemsLinks, index).focus();
                    break;
                // Close menu.
                case KEY.TAB:
                    _closeMenu(this);
                    // TODO
                    // What has to happen here? In speed menu, tabbing backward
                    // will give focus to Play/Pause button and tabbing
                    // forward to Volume button.
                    break;
                // Close menu, give focus to button and change
                // file type.
                case KEY.ENTER:
                case KEY.SPACE:
                    this.button.focus();
                    this.changeFileType.call(this, event);
                    _closeMenu(this);
                    break;
                // Close menu and give focus to speed control.
                case KEY.ESCAPE:
                    _closeMenu(this);
                    this.button.focus();
                    break;
            }
            return false;
        }
        else {
            switch(keyCode) {
                // Open menu and focus on last element of list above it.
                case KEY.ENTER:
                case KEY.SPACE:
                case KEY.UP:
                    _openMenu(this);
                    this.menuItemsLinks.last().focus();
                    break;
                // Close menu.
                case KEY.ESCAPE:
                    _closeMenu(this);
                    break;
            }
            // We do not stop propagation and default behavior on a TAB
            // keypress.
            return event.keyCode === KEY.TAB;
        }
    }

    /**
     * @desc Bind any necessary function callbacks to DOM events (click,
     *     mousemove, etc.).
     *
     * @type {function}
     * @access private
     *
     * @param {object} state The object containg the state of the video player.
     *     All other modules, their parameters, public variables, etc. are
     *     available via this object.
     *
     * @this {object} The global window object.
     *
     * @returns {undefined}
     */
    function _bindHandlers(state) {
        var menu = state.videoAccessibleMenu;

        // Attach various events handlers to menu container.
        menu.container.on({
            'mouseenter': _openMenuHandler.bind(menu),
            'mouseleave': _closeMenuHandler.bind(menu),
            'click': _toggleMenuHandler.bind(menu),
            'keydown': _keyDownHandler.bind(menu)
        });

        // Attach click and keydown event handlers to individual menu items.
        menu.menuItems
            .on('click', 'a.a11y-menu-item-link', _clickHandler.bind(menu))
            .on('keydown', 'a.a11y-menu-item-link', _keyDownHandler.bind(menu));
    }

    function setValue(value) {
        var menu = this.videoAccessibleMenu;

        menu.value = value;
        menu.menuItems
            .removeClass('active')
            .find("a[data-value='" + value + "']")
            .parent()
            .addClass('active');
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this'
    // keyword) is the 'state' object. The magic private function that makes
    // them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function changeFileType(event) {
        var fileType = $(event.currentTarget).data('value');

        this.videoAccessibleMenu.setValue(fileType);
        this.saveState(true, {'transcript_download_format': fileType});
        this.storage.setItem('transcript_download_format', fileType);
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
