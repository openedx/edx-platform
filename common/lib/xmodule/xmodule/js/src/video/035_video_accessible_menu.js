(function (define) {

// VideoAccessibleMenu module.
define(
'video/035_video_accessible_menu.js',
['video/00_component.js'],
function (Component) {
    var AbstractMenu, Menu, Submenu, MenuItem;

    AbstractMenu = Component.extend({
        initialize: function (container, options) {
            this.options = {
                menuClass: 'specific-menu-class',
                itemClass: 'specific-menu-item-class',
                items: {},

                name: '',
                dataAttrs: {options: options, menu: this},
                attrs: {},
                callback: $.noop
            };

            $.extend(true, this.options, options);
            this.childs = [];
            this.element = this.createElement();
            this.delegateEvents();
        },

        createElement: function () {
            return null;
        },


        remove: function () {
            this.element.removeNode(true);
        },

        addChild: function (child) {
            this.childs.push(child);
            child.parent = this;
        },

        getChilds: function () {
            // Returns the copy.
            return this.childs.concat();
        },

        getElement: function () {
            return this.element;
        },

        show: function () {
            var fragment = document.createDocumentFragment();

            _.each(this.getChilds(), function (child) {
                fragment.appendChild(child.show()[0]);
            }, this);

            this.getElement().append([fragment]);
            return this.getElement();
        },

        open: function () { },
        close: function () { },

        delegateEvents: function () {
            this.getElement().on('keydown', '> li', this.itemHandler.bind(this));
        },

        openHandler: function (event) {},
        closeHandler: function (event) {},

        // Get previous element in array or cycles back to the last if it is the
        // first.
        previousItem: function (index) {
            var childs = this.getChilds();
            return childs[index < 1 ? childs.length - 1 : index - 1].getElement();
        },

        // Get next element in array or cycles back to the first if it is the last.
        nextItem: function (index) {
            var childs = this.getChilds();
            return childs[index >= childs.length - 1 ? 0 : index + 1].getElement();
        },

        isItemsFocused: function () {
            // var childs = this.getChilds();
            // return $(childs).is(':focus');
        },

        itemHandler: function (event) {
            var callback = this.options.callback,
                data, key, options;

            // if ($.isFunction(callback)) {
                event.preventDefault();
                data = $(event.currentTarget).data();
                key = data.key;
                options = data.options;
                switch(event.type) {
                    case 'click':
                        // callback.call(this, key, options);
                        break;
                    case 'keydown':
                        this.keyDownHandler.call(this, event);
                        break;
                }
            // }
        },

        keyDownHandler: function (event) {
            var KEY = $.ui.keyCode,
                keyCode = event.keyCode,
                target = $(event.currentTarget),
                index;

            index = target.index();
            switch (keyCode) {
                // Scroll up menu, wrapping at the top. Keep menu open.
                case KEY.UP:
                    this.previousItem(index).focus();
                    break;
                // Scroll down  menu, wrapping at the bottom. Keep menu
                // open.
                case KEY.DOWN:
                    this.nextItem(index).focus();
                    break;
                // Close menu.
                case KEY.TAB:
                    this.close();
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
                    this.close();
                    break;
                // Close menu and give focus to speed control.
                case KEY.ESCAPE:
                    this.close();
                    // this.button.focus();
                    break;
            }
            return false;
        }
    });

    Menu = AbstractMenu.extend({
        createElement: function () {
            return $('<ol />', {
                'class': 'menu',
                'role': 'menu'
            }).data({'menu': this});
        }
    });

    Submenu = AbstractMenu.extend({
        createElement: function () {
            var element = $('<li />', {
                'class': ['menu-item', this.options.itemClass].join(' '),
                'aria-disabled': 'false',
                'role': 'menuitem',
                'tabindex': 0,
                'text': this.options.name
            }).attr(this.options.attrs).data(this.options.dataAttrs);

            this.list = $('<ol />', {
                'class': 'menu',
                'role': 'menu'
            });

            element.append(this.list);
            return element;
        }
    });

    Submenu.prototype = {
        show: function () {
            var fragment = document.createDocumentFragment();

            _.each(this.getChilds(), function (child) {
                fragment.appendChild(child.show()[0]);
            }, this);

            this.list.append([fragment]);
            return this.getElement();
        },

        keyDownHandler: function (event) {
            var KEY = $.ui.keyCode,
                keyCode = event.keyCode;

            switch (keyCode) {
                case KEY.RIGHT:
                    if (this.getChilds()[0]) {
                      this.getChilds()[0].getElement().focus();
                    }
                    break;

                case KEY.LEFT:
                    if (this.parent) {
                      this.parent.getElement().focus();
                    }
                    break;
            };

            return this.__super__.keyDownHandler.apply(this);
        }
    };

    MenuItem = function (options) {
        this.options = $.extend(true, {
            name: '',
            itemClass: '',
            dataAttrs: {options: options, menu: this},
            attrs: {},
            callback: $.noop
        }, options);

        this.element = $('<li />', {
            'class': ['menu-item', this.options.itemClass].join(' '),
            'aria-disabled': 'false',
            'role': 'menuitem',
            'tabindex': 0,
            'text': this.options.name
        }).attr(this.options.attrs).data(this.options.dataAttrs);
        this.delegateEvents();
    };

    MenuItem.prototype = {
        addChild: function () { },

        getChilds: function () { },

        show: function () {
            return this.getElement();
        },

        getElement: function () {
            return this.element;
        },

        delegateEvents: function () {
            this.getElement().on('click keydown', this.itemHandler.bind(this));
            return this;
        },

        setAttrs: function (attrs) {
            this.getElement().attr(attrs);
            return this;
        },

        setDataAttrs: function (dataAttrs) {
            this.getElement().data(dataAttrs);
            return this;
        },

        getDataAttrs: function () {
            return this.getElement().data();
        },

        setName: function (name) {
            this.getElement().text(name);
            return this;
        },

        itemHandler: function (event) {
            var callback = this.options.callback,
                options;

            if ($.isFunction(callback)) {
                event.preventDefault();
                options = this.options;
                switch(event.type) {
                    case 'click':
                    // case 'keydown':
                        callback.call(this, event, this, options);
                        break;
                }
            }
        }
    };

    // VideoAccessibleMenu() function - what this module 'exports'.
    return function (state) {
        var speedCallback = function (event, menuitem, options) {
                var speed = parseFloat(options.name);
                state.videoCommands.execute('speed', speed);
            },
            options = {
                items: {
                    'play': {
                        name: 'Play', attrs: {title: 'aaaa'}, dataAttrs: {aaaa: 'bbbb'},
                        callback: function (event, menuitem) {
                            if (state.videoCommands.execute('togglePlayback')) {
                                menuitem.setName('Pause');
                            } else {
                                menuitem.setName('Play');
                            }
                        }
                    },
                    'mute': {
                        name: 'Mute',
                        callback: function (event, menuitem) {
                            if (state.videoCommands.execute('toggleMute')) {
                                menuitem.setName('Mute');
                            } else {
                                menuitem.setName('Unmute');
                            }
                        }
                    },
                    'fullscreen': {
                        name: 'Go to fullscreen mode',
                        callback: function (event, menuitem) {
                            if (state.videoCommands.execute('toggleFullScreen')) {
                                menuitem.setName('Go to fullscreen mode');
                            } else {
                                menuitem.setName('Exit from fullscreen mode');
                            }
                        }
                    },
                    'speed': {
                        items: {
                            '0.75': {name: '0.75x', callback: speedCallback},
                            '1.0': {name: '1.0x', callback: speedCallback},
                            '1.25': {name: '1.25x', callback: speedCallback},
                            '1.5': {name: '1.5x', callback: speedCallback},
                        }
                    }
                }
            };

        var topMenu = new Menu();
        // Do that on first menu invocation.
        (function build(container, options) {
            _.each(options, function(item) {
                var child;
                if (_.has(item, 'items')) {
                    child = build((new Submenu(item)), item.items);
                } else {
                    child = new MenuItem(item);
                }
                container.addChild(child);
            }, this);

            return container;
        } (topMenu, options.items));

        $('.video').append(topMenu.show());

        return $.Deferred().resolve().promise();
    };
});

}(RequireJS.define));
