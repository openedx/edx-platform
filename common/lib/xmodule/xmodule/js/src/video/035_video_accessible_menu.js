(function(define) {
'use strict';
// VideoAccessibleMenu module.
define(
'video/035_video_accessible_menu.js', [],
function() {
    /**
     * Video Download Transcript control module.
     * @exports video/035_video_accessible_menu.js
     * @constructor
     * @param {jquery Element} element
     * @param {Object} options
     */
    var VideoAccessibleMenu = function(element, options) {
        if (!(this instanceof VideoAccessibleMenu)) {
            return new VideoAccessibleMenu(element, options);
        }

        _.bindAll(this, 'openMenu', 'openMenuHandler', 'closeMenu', 'closeMenuHandler', 'toggleMenuHandler',
            'clickHandler', 'keyDownHandler', 'render', 'menuItemsLinksFocused', 'changeFileType', 'setValue'
        );

        this.container = element;
        this.options = options || {};

        if (this.container.find('.video-tracks')) {
            this.initialize();
        }
    };

    VideoAccessibleMenu.prototype = {
        /** Initializes the module. */
        initialize: function() {
            this.value = this.options.storage.getItem('transcript_download_format');
            this.el = this.container.find('.video-tracks .a11y-menu-container');
            this.render();
            this.bindHandlers();
        },

        /**
         * Creates any necessary DOM elements, attach them, and set their,
         * initial configuration.
         */
        render: function() {
            var value, msg;
            // For the  time being, we assume that the menu structure is present in
            // the template HTML. In the future accessible menu plugin, everything
            // inside <div class='menu-container'></div> will be generated in this
            // file.
            this.button = this.el.children('.a11y-menu-button');
            this.menuList = this.el.children('.a11y-menu-list');
            this.menuItems = this.menuList.children('.a11y-menu-item');
            this.menuItemsLinks = this.menuItems.children('.a11y-menu-item-link');
            value = (function (val, activeElement) {
                return val || activeElement.find('a').data('value') || 'srt';
            }(this.value, this.menuItems.filter('.active')));
            msg = '.' + value;

            if (value) {
                this.setValue(value);
                this.button.text(gettext(msg));
            }
        },

        /** Bind any necessary function callbacks to DOM events. */
        bindHandlers: function() {
            // Attach various events handlers to menu container.
            this.el.on({
                'mouseenter': this.openMenuHandler,
                'mouseleave': this.closeMenuHandler,
                'click': this.toggleMenuHandler,
                'keydown': this.keyDownHandler
            });

            // Attach click and keydown event handlers to individual menu items.
            this.menuItems
                .on('click', 'a.a11y-menu-item-link', this.clickHandler)
                .on('keydown', 'a.a11y-menu-item-link', this.keyDownHandler);
        },

        // Get previous element in array or cyles back to the last if it is the
        // first.
        previousMenuItemLink: function(links, index) {
            return index < 1 ? links.last() : links.eq(index - 1);
        },

        // Get next element in array or cyles back to the first if it is the last.
        nextMenuItemLink: function(links, index) {
            return index >= links.length - 1 ? links.first() : links.eq(index + 1);
        },

        menuItemsLinksFocused: function() {
            return this.menuItemsLinks.is(':focus');
        },

        openMenu: function(withoutHandler) {
            // When menu items have focus, the menu stays open on
            // mouseleave. A closeMenuHandler is added to the window
            // element to have clicks close the menu when they happen
            // outside of it. We namespace the click event to easily remove it (and
            // only it) in closeMenu.
            this.el.addClass('open');
            this.button.text('...');
            if (!withoutHandler) {
                $(window).on('click.currentMenu', this.closeMenuHandler);
            }
            // @TODO: onOpen callback
        },

        closeMenu: function(withoutHandler) {
            // Remove the previously added clickHandler from window element.
            var msg = '.' + this.value;

            this.el.removeClass('open');
            this.button.text(gettext(msg));
            if (!withoutHandler) {
                $(window).off('click.currentMenu');
            }
            // @TODO: onClose callback
        },

        openMenuHandler: function() {
            this.openMenu(true);
            return false;
        },

        closeMenuHandler: function(event) {
            // Only close the menu if no menu item link has focus or `click` event.
            if (!this.menuItemsLinksFocused() || event.type === 'click') {
                this.closeMenu(true);
            }
            return false;
        },

        toggleMenuHandler: function() {
            if (this.el.hasClass('open')) {
                this.closeMenu(true);
            } else {
                this.openMenu(true);
            }
            return false;
        },

        // Various event handlers. They all return false to stop propagation and
        // prevent default behavior.
        clickHandler: function(event) {
            this.changeFileType.call(this, event);
            this.closeMenu(true);
            return false;
        },

        keyDownHandler: function(event) {
            var KEY = $.ui.keyCode,
                keyCode = event.keyCode,
                target = $(event.currentTarget),
                index;

            if (target.is('a.a11y-menu-item-link')) {
                index = target.parent().index();
                switch (keyCode) {
                    // Scroll up menu, wrapping at the top. Keep menu open.
                    case KEY.UP:
                        this.previousMenuItemLink(this.menuItemsLinks, index).focus();
                        break;
                    // Scroll down  menu, wrapping at the bottom. Keep menu
                    // open.
                    case KEY.DOWN:
                        this.nextMenuItemLink(this.menuItemsLinks, index).focus();
                        break;
                    // Close menu.
                    case KEY.TAB:
                        this.closeMenu();
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
                        this.closeMenu();
                        break;
                    // Close menu and give focus to speed control.
                    case KEY.ESCAPE:
                        this.closeMenu();
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
                        this.openMenu();
                        this.menuItemsLinks.last().focus();
                        break;
                    // Close menu.
                    case KEY.ESCAPE:
                        this.closeMenu();
                        break;
                }
                // We do not stop propagation and default behavior on a TAB
                // keypress.
                return event.keyCode === KEY.TAB;
            }
        },

        setValue: function(value) {
            this.value = value;
            this.menuItems
                .removeClass('active')
                .find("a[data-value='" + value + "']")
                .parent()
                .addClass('active');
        },

        changeFileType: function(event) {
            var fileType = $(event.currentTarget).data('value'),
                data = {'transcript_download_format': fileType};

            this.setValue(fileType);
            this.options.storage.setItem('transcript_download_format', fileType);

            $.ajax({
                url: this.options.saveStateUrl,
                type: 'POST',
                dataType: 'json',
                data: data
            });
        }
    };

    return VideoAccessibleMenu;
});
}(RequireJS.define));
