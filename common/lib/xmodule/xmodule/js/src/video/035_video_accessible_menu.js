(function (define) {

// VideoAccessibleMenu module.
define(
'video/035_video_accessible_menu.js',
['video/00_component.js'],
function (Component) {
    var AbstractMenu, Menu, Submenu, MenuItem;

    var DEBUG_KEYDOWN_EVENTS = false;
    var DEBUG_MOUSE_EVENTS = false;

    AbstractMenu = Component.extend({
        initialize: function (options) {
            this.options = {
                id: _.uniqueId(),
                prefix: 'prefix-',
                items: {},
                label: '',
                dataAttrs: {menu: this},
                attrs: {},
                callback: $.noop
            };

            $.extend(true, this.options, options);
            this.children = [];
            this.element = this.createElement();
            this.delegateEvents();
        },

        delegateEvents: function () {
            this.getElement().on('keydown mouseleave mouseover', '.menu-item', this.itemHandler.bind(this));
        },

        createElement: function () {
            return null;
        },

        remove: function () {
            this.getElement().remove();
        },

        addChild: function (child) {
            var firstChild = null, lastChild = null;
            if (this.hasChildren()) {
                lastChild = this.getLastChild();
                lastChild.next = child;
                firstChild = this.getFirstChild();
                firstChild.prev = child;
            }
            child.parent = this;
            child.next = firstChild;
            child.prev = lastChild;
            this.children.push(child);
        },

        getChildren: function () {
            // Returns the copy.
            return this.children.concat();
        },

        hasChildren: function () {
            return this.getChildren().length > 0;
        },

        getFirstChild: function () {
            return this.children[0];
        },

        getLastChild: function () {
            var len = this.children.length;
            return this.children[len - 1];
        },

        getElement: function () {
            return this.element;
        },

        populateElement: function () {
            var fragment = document.createDocumentFragment();

            _.each(this.getChildren(), function (child) {
                fragment.appendChild(child.populateElement()[0]);
            }, this);

            this.appendContent([fragment]);
            return this.getElement();
        },

        open: function () { },
        close: function () { },
        openHandler: function (event) { },
        closeHandler: function (event) { },

        itemHandler: function (event) {
            event.preventDefault();
            var item = $(event.currentTarget).data('menu');
            switch(event.type) {
                case 'keydown':
                    this.keyDownHandler.call(this, event, item);
                    break;
                case 'mouseover':
                    this.mouseOverHandler.call(this, event, item);
                    break;
                case 'mouseleave':
                    this.mouseLeaveHandler.call(this, event, item);
                    break;
            }
        },

        keyDownHandler: function () { },
        mouseOverHandler: function () { },
        mouseLeaveHandler: function () { }
    });

    Menu = AbstractMenu.extend({
        createElement: function () {
            return $('<ol />', {
                'class': ['menu', this.options.prefix + 'menu'].join(' '),
                'role': 'menu'
            });
        },

        appendContent: function (content) {
            this.getElement().append(content);
        },

        focus: function () {
            if (this.hasChildren()) {
                this.getChildren()[0].focus();
            }
            return this;
        },

        keyDownHandler: function (event, item) {
            var KEY = $.ui.keyCode,
                keyCode = event.keyCode;

            if (DEBUG_KEYDOWN_EVENTS) {debugger;}

            switch (keyCode) {
                case KEY.UP:
                    item.prev.focus();
                    event.stopPropagation();
                    break;
                case KEY.DOWN:
                    item.next.focus();
                    event.stopPropagation();
                    break;
                case KEY.TAB:
                    event.stopPropagation();
                    break;
                case KEY.ESCAPE:
                    this.close();
                    break;
            }

            return false;
        }
    });

    Submenu = AbstractMenu.extend({
        createElement: function () {
            var element = $('<li />', {
                'class': ['submenu-item','menu-item', this.options.prefix + 'submenu-item'].join(' '),
                'aria-disabled': 'false',
                'role': 'menu',
                'tabindex': 0,
                'text': this.options.label
            }).attr(this.options.attrs).data(this.options.dataAttrs);

            this.list = $('<ol />', {
                'class': ['menu', 'submenu', this.options.prefix + 'submenu'].join(' '),
                'aria-disabled': 'false',
                'role': 'presentation'
            });

            element.append(this.list);
            return element;
        },

        delegateEvents: function () {
            this.getElement().on('keydown mouseleave mouseover', this.itemHandler.bind(this));
        },

        appendContent: function (content) {
            this.list.append(content);
        },

        open: function () {
            this.getElement().addClass('is-opened');
            this.getChildren()[0].focus();
        },

        close: function () {
            this.getElement().removeClass('is-opened');
            this.focus();
        },

        focus: function () {
            this.getElement().focus();
            return this;
        },

        keyDownHandler: function (event) {
            var KEY = $.ui.keyCode,
                keyCode = event.keyCode;

            if (DEBUG_KEYDOWN_EVENTS) {debugger;}
            switch (keyCode) {
                case KEY.RIGHT:
                    this.open();
                    event.stopPropagation();
                    break;
                case KEY.LEFT:
                    this.close();
                    event.stopPropagation();
                    break;
                case KEY.ENTER:
                case KEY.SPACE:
                    this.open();
                    event.stopPropagation();
                    break;
            }

            return false;
        },

        mouseOverHandler: function () {
            if (DEBUG_MOUSE_EVENTS) {debugger;}
            this.open();
        },

        mouseLeaveHandler: function () {
            if (DEBUG_MOUSE_EVENTS) {debugger;}
            this.close();
        }
    });

    MenuItem = function (options) {
        this.options = $.extend(true, {
            label: '',
            itemClass: '',
            dataAttrs: {menu: this},
            attrs: {},
            callback: $.noop
        }, options);

        this.element = $('<li />', {
            'class': ['menu-item', this.options.prefix + 'menu-item'].join(' '),
            'aria-disabled': 'false',
            'role': 'menuitem',
            'tabindex': 0,
            'text': this.options.label
        }).attr(this.options.attrs).data(this.options.dataAttrs);
        this.delegateEvents();
    };

    MenuItem.prototype = {
        addChild: function () { },

        getChildren: function () { },

        populateElement: function () {
            return this.getElement();
        },

        getElement: function () {
            return this.element;
        },

        delegateEvents: function () {
            this.getElement().on('click keydown', this.itemHandler.bind(this));
            return this;
        },

        setLabel: function (label) {
            this.getElement().text(label);
            return this;
        },

        focus: function () {
            this.getElement().focus();
            return this;
        },

        activate: function () {
            var callback = this.options.callback;

            if ($.isFunction(callback)) {
                callback.call(this, event, this, this.options);
                this.parent.close();
                // this.getElement().addClass('is-active');
            }
        },

        unactivate: function () {
            this.getElement().removeClass('is-active');
        },

        itemHandler: function (event) {
            event.preventDefault();
            switch(event.type) {
                case 'click':
                    this.activate();
                    break;

                case 'keydown':
                    this.keyDownHandler.call(this, event);
                    break;
            }
        },

        keyDownHandler: function (event) {
            var KEY = $.ui.keyCode,
                keyCode = event.keyCode;

            if (DEBUG_KEYDOWN_EVENTS) {debugger;}
            switch (keyCode) {
                case KEY.RIGHT:
                    event.stopPropagation();
                    break;
                case KEY.ENTER:
                case KEY.SPACE:
                    this.activate();
                    event.stopPropagation();
                    break;
            }

            return false;
        }
    };

    // VideoAccessibleMenu() function - what this module 'exports'.
    return function (state) {

        var speedCallback = function (event, menuitem, options) {
                var speed = parseFloat(options.label);
                state.videoCommands.execute('speed', speed);
            },
            options = {
                items: {
                    'play': {
                        label: 'Play', attrs: {title: 'aaaa'}, dataAttrs: {aaaa: 'bbbb'},
                        callback: function (event, menuitem) {
                            if (state.videoCommands.execute('togglePlayback')) {
                                menuitem.setLabel('Pause');
                            } else {
                                menuitem.setLabel('Play');
                            }
                        }
                    },
                    'mute': {
                        label: state.videoVolumeControl.getMuteStatus() ? 'Unmute' : 'Mute',
                        callback: function (event, menuitem) {
                            if (state.videoCommands.execute('toggleMute')) {
                                menuitem.setLabel('Unmute');
                            } else {
                                menuitem.setLabel('Mute');
                            }
                        }
                    },
                    'fullscreen': {
                        label: 'Go to fullscreen mode',
                        callback: function (event, menuitem) {
                            if (state.videoCommands.execute('toggleFullScreen')) {
                                menuitem.setLabel('Exit from fullscreen mode');
                            } else {
                                menuitem.setLabel('Go to fullscreen mode');
                            }
                        }
                    },
                    'speed': {
                        label: 'Speed',
                        items: {
                            '0.75': {label: '0.75x', callback: speedCallback},
                            '1.0': {label: '1.0x', callback: speedCallback},
                            '1.25': {label: '1.25x', callback: speedCallback},
                            '1.5': {label: '1.5x', callback: speedCallback},
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

        $('.video').append(topMenu.populateElement());

        return $.Deferred().resolve().promise();
    };
});

}(RequireJS.define));
