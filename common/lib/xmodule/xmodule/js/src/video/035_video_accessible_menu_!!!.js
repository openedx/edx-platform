(function (define) {

// VideoAccessibleMenu module.
define(
'video/035_video_accessible_menu.js',
[],
function () {
    var Menu, MenuItem;
    // menuClass: 'specific-menu-class',
    // itemClass: 'specific-menu-item-class',
    // callback: function (key, value) {},
    // items: {
    //     'edit': {name: 'Edit', attrs: {}, data: {}},
    //     'cut': {name: 'Cut'},
    //     'copy': {name: 'Copy'},
    //     'paste': {name: 'Paste'},
    //     'delete': {name: 'Delete'},
    //     'sep1': {items: {
    //          'subkey': {name: 'SubName'},
    //      }},
    //     'quit': {name: 'Quit'}
    // }
    Menu = function (container, options) {
        this.options = {
            menuClass: 'specific-menu-class',
            itemClass: 'specific-menu-item-class',
            callback: {},
            items: {}
        };

        $.extend(true, this.options, options);
        this.initialize(container);
    };

    Menu.prototype = {
        initialize: function (container) {
            this.el = this.getMenuList(null, true);
            this.build(this.el, this.options.items)
                .addClass(this.options.menuClass)
                .appendTo(container);

            this.delegateEvents();
        },

        delegateEvents: function () {
            this.getElement().on('click keydown', '.menu-item', this.itemHandler.bind(this));
        },

        show: function () {},
        hide: function () {},
        showHandler: function (event) {},
        hideHandler: function (event) {},

        getElement: function () {
            return this.el;
        },

        getMenuItem: function (options, key) {
            // return new MenuItem(key, options).getElement();
            var opts = $.extend(true, {
                name: '',
                itemClass: '',
                dataAttrs: {key: key, options: options},
                attrs: {}
            }, options);

            var el = $('<li />', {
                'class': ['menu-item', opts.itemClass].join(' '),
                'aria-disabled': 'false',
                'role': 'menuitem',
                'tabindex': 0,
                'text': opts.name
            }).attr(opts.attrs).data(opts.dataAttrs);

            // var anchor = $('<a />', {
            //     'href': '#',
            //     'class': 'menu-item-link',
            //     'aria-disabled': 'false',
            //     'role': 'menuitem',
            //     'text': opts.name
            // }).appendTo(el);

            return el;
        },

        getMenuList: function (options, topmenu) {
            var list = $('<ol />', {
                    'class': topmenu ? 'menu': 'submenu',
                    'role': 'menu'
                });

            if (topmenu) {
                return list;
            } else {
                this.build(list, options.items);
                return this.getMenuItem().append(list);
            }
        },

        build: function (container, data) {
            _.each(data, function(item, key) {
                var element;
                if (_.has(item, 'items')) {
                    element = this.getMenuList(item);
                } else {
                    element = this.getMenuItem(item, key);
                }
                container.append(element);
            }, this);

            return container;
        },

        // Get previous element in array or cycles back to the last if it is the
        // first.
        previousItem: function (list, index) {
            return list.eq(index < 1 ? list.length - 1 : index - 1);
        },

        // Get next element in array or cycles back to the first if it is the last.
        nextItem: function (list, index) {
            return list.eq(index >= list.length - 1 ? 0 : index + 1);
        },

        isItemsFocused: function (list) {
            return list.is(':focus');
        },

        itemHandler: function (event) {
            var callback = this.options.callback,
                data, key, options;

            if ($.isFunction(callback)) {
                event.preventDefault();
                data = $(event.currentTarget).data();
                key = data.key;
                options = data.options;
                switch(event.type) {
                    case 'click':
                        callback.call(this, key, options);
                        break;
                    case 'keydown':
                        this.keyDownHandler.call(this, event);
                        break;
                }
            }
        },

        keyDownHandler: function (event) {
            var KEY = $.ui.keyCode,
                keyCode = event.keyCode,
                target = $(event.currentTarget),
                list = target.closest('.submenu, .menu').children(),
                index;
            // if (target.is('a.a11y-menu-item-link')) {
                index = target.index();
                switch (keyCode) {
                    // Scroll up menu, wrapping at the top. Keep menu open.
                    case KEY.UP:
                        this.previousItem(list, index).focus();
                        break;
                    // Scroll down  menu, wrapping at the bottom. Keep menu
                    // open.
                    case KEY.DOWN:
                        this.nextItem(list, index).focus();
                        break;

                    // Close Submenu
                    case KEY.LEFT:
                        target.parents('.menu-item').first().focus();
                        break;

                    // Open Submenu
                    case KEY.RIGHT:
                        target.find('> .submenu > .menu-item').first().focus();
                        break;
                    // Close menu.
                    case KEY.TAB:
                        this.hide();
                        // TODO
                        // What has to happen here? In speed menu, tabbing backward
                        // will give focus to Play/Pause button and tabbing
                        // forward to Volume button.
                        break;
                    // Close menu, give focus to button and change
                    // file type.
                    case KEY.ENTER:
                    case KEY.SPACE:
                        // this.button.focus();
                        // this.changeFileType.call(this, event);
                        this.hide();
                        break;
                    // Close menu and give focus to speed control.
                    case KEY.ESCAPE:
                        this.hide();
                        // this.button.focus();
                        break;
                }
                return false;
            // } else {
            //     switch(keyCode) {
            //         // Open menu and focus on last element of list above it.
            //         case KEY.ENTER:
            //         case KEY.SPACE:
            //         case KEY.UP:
            //             this.show();
            //             list.last().focus();
            //             break;
            //         // Close menu.
            //         case KEY.ESCAPE:
            //             this.hide();
            //             break;
            //     }
            //     // We do not stop propagation and default behavior on a TAB
            //     // keypress.
            //     return event.keyCode === KEY.TAB;
            // }
        },

    };

    // MenuItem = function (key, options) {
    //     this.options = $.extend(true, {
    //         name: '',
    //         itemClass: '',
    //         dataAttrs: {key: key, options: options, menuitem: this},
    //         attrs: {}
    //     }, options);

    //     this.el = $('<li />', {
    //         'class': ['menu-item', this.options.itemClass].join(' '),
    //         'role': 'presentation'
    //     }).attr(this.options.attrs).data(this.options.dataAttrs);

    //     this.anchor = $('<a />', {
    //         'href': '#',
    //         'class': 'menu-item-link',
    //         'aria-disabled': 'false',
    //         'role': 'menuitem',
    //         'text': this.options.name
    //     }).appendTo(this.el);

    //     this.delegateEvents();
    // };

    // MenuItem.prototype = {
    //     getElement: function () {
    //         return this.el;
    //     },

    //     getAnchor: function () {
    //         return this.anchor;
    //     },

    //     delegateEvents: function () {
    //         this.getElement().on('click', 'a', this.itemHandler.bind(this));
    //     },

    //     setAttrs: function (attrs) {
    //         this.getElement().attr(attrs);
    //         return this;
    //     },

    //     setDataAttrs: function (dataAttrs) {
    //         this.getElement().data(dataAttrs);
    //         return this;
    //     },

    //     setName: function (name) {
    //         this.getAnchor().text(name);
    //         return this;
    //     },

    //     setKey: function (key) {
    //         this.setDataAttrs({key: key});
    //         return this;
    //     },
    // };

    // VideoAccessibleMenu() function - what this module 'exports'.
    return function (state) {
        (new Menu('.video', {
            callback: function (key, options) {
                switch(key) {
                    case 'play':
                        state.videoCommands.execute('play');
                        menuitem.setName('pause').setKey('pause');
                        break;
                    case 'pause':
                        state.videoCommands.execute('pause');
                        menuitem.setName('play').setKey('play');
                        break;
                    case 'mute':
                        state.videoCommands.execute('mute');
                        menuitem.setName('unmute').setKey('unmute');
                        break;
                    case 'unmute':
                        state.videoCommands.execute('unmute');
                        menuitem.setName('mute').setKey('mute');
                        break;
                    case 'fullscreen':
                        state.videoCommands.execute('toggleFullScreen');
                        break;
                    case '0.75':
                        state.videoCommands.execute('speed', 0.75);
                        break;
                    case '1.0':
                        state.videoCommands.execute('speed', 1);
                        break;
                    case '1.25':
                        state.videoCommands.execute('speed', 1.25);
                        break;
                    case '1.5':
                        state.videoCommands.execute('speed', 1.5);
                        break;
                }
            },
            items: {
                'play': {name: 'play', attrs: {title: 'aaaa'}, dataAttrs: {aaaa: 'bbbb'}},
                // 'pause': {name: 'pause'},
                'mute': {name: 'mute'},
                // 'unmute': {name: 'unmute'},
                'fullscreen': {name: 'fullscreen'},
                'speed': {
                    items: {
                        '0.75': {name: '0.75x'},
                        '1.0': {name: '1.0x'},
                        '1.25': {name: '1.25x'},
                        '1.5': {name: '1.5x'},
                    }
                }
            }
        }));

        return $.Deferred().resolve().promise();
    };
});

}(RequireJS.define));
