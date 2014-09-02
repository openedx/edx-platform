(function (define) {

// VideoAccessibleMenu module.
define(
'video/035_video_accessible_menu.js',
['video/00_component.js'],
function (Component) {
    var AbstractItem, AbstractMenu, Menu, Submenu, MenuItem;

    var DEBUG_KEYDOWN_EVENTS = true;
    var DEBUG_MOUSE_EVENTS = false;

    AbstractItem = Component.extend({
        addChild: function () { },
        close: function () { },
        getChildren: function () { },
        createElement: function () {
            return null;
        },
        populateElement: function () { },
        remove: function () { },
        focus: function () { },
        activate: function () { },
        unactivate: function () { },
        siblings: function () { },
        disable: function () { },
        enable: function () { },
        itemHandler: function (event) { },
        keyDownHandler: function (event) { }
    });

    AbstractMenu = AbstractItem.extend({
        initialize: function (options) {
            this.options = {
                prefix: 'prefix-',
                items: [],
                label: '',
                dataAttrs: {menu: this},
                attrs: {},
                callback: $.noop
            };

            $.extend(true, this.options, options);
            this.id = _.uniqueId();
            this.children = [];
            this.element = this.createElement();
            this.delegateEvents();
        },

        delegateEvents: function () {
            this.getElement().on('keydown mouseleave mouseover', '.menu-item', this.itemHandler.bind(this));
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
            return _.last(this.children);
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
        close: function () {
            _.each(this.getChildren(), function (child) {
                child.close();
            }, this);
            this.getElement().removeClass('is-opened');
        },
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

        open: function () {
            this.getElement().addClass('is-opened');
            this.getChildren()[0].focus();
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

        unactivate: function () {},

        appendContent: function (content) {
            this.list.append(content);
        },

        open: function () {
            this.getElement().addClass('is-opened');
            this.getChildren()[0].focus();
        },

        close: function () {
            AbstractMenu.prototype.close.call(this);
            this.focus();
        },

        focus: function () {
            this.getElement().focus();
            return this;
        },

        disable: function () {
            this.getElement().addClass('is-disabled');
        },

        enable: function () {
            this.getElement().removeClass('is-disabled');
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
                    this.parent.close();
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

    MenuItem = AbstractItem.extend({
        initialize: function (options) {
            this.options = $.extend(true, {
                label: '',
                prefix: 'prefix-',
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
            this.id = _.uniqueId();
            this.delegateEvents();
        },
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
                this.getElement().addClass('is-active');
                _.each(this.siblings(), function (sibling) {
                    sibling.unactivate();
                });
                this.getRoot().close();
            }
        },

        unactivate: function () {
            this.getElement().removeClass('is-active');
        },

        siblings: function () {
            var items = [],
                item = this;
            while (item.next && item.next.id !== this.id) {
                item = item.next;
                items.push(item);
            }

            return items;
        },

        disable: function () {
            this.getElement().addClass('is-disabled');
        },

        enable: function () {
            this.getElement().removeClass('is-disabled');
        },

        // @TODO pass as argument?
        getRoot: function () {
            var item = null;
            return function () {
                if (item) {
                    return item;
                }

                item = this;
                do {
                    item = item.parent;
                } while (item.parent);

                return item;
            };
        }(),

        itemHandler: function (event) {
            event.preventDefault();
            switch(event.type) {
                case 'click':
                    this.activate();
                    break;
                case 'keydown':
                    this.keyDownHandler.call(this, event, this);
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
                case KEY.LEFT:
                    this.parent.close();
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
    });

    // VideoAccessibleMenu() function - what this module 'exports'.
    return function (state) {

        var speedCallback = function (event, menuitem, options) {
                var speed = parseFloat(options.label);
                state.videoCommands.execute('speed', speed);
            },
            options = {
                items: [{
                        label: 'Play', attrs: {title: 'aaaa'}, dataAttrs: {aaaa: 'bbbb'},
                        callback: function (event, menuitem) {
                            if (state.videoCommands.execute('togglePlayback')) {
                                menuitem.setLabel('Pause');
                            } else {
                                menuitem.setLabel('Play');
                            }
                        }
                    }, {
                        label: state.videoVolumeControl.getMuteStatus() ? 'Unmute' : 'Mute',
                        callback: function (event, menuitem) {
                            if (state.videoCommands.execute('toggleMute')) {
                                menuitem.setLabel('Unmute');
                            } else {
                                menuitem.setLabel('Mute');
                            }
                        }
                    }, {
                        label: 'Go to fullscreen mode',
                        callback: function (event, menuitem) {
                            if (state.videoCommands.execute('toggleFullScreen')) {
                                menuitem.setLabel('Exit from fullscreen mode');
                            } else {
                                menuitem.setLabel('Go to fullscreen mode');
                            }
                        }
                    }, {
                        label: 'Speed',
                        items: [
                            {label: '0.75x', callback: speedCallback},
                            {label: '1.0x', callback: speedCallback},
                            {label: '1.25x', callback: speedCallback},
                            {label: '1.5x', callback: speedCallback, items: [
                                {label: 'AAAA'}, {label: 'BBBB'}
                            ]},
                        ]
                    }
                ]
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

        $('.video')
            .append(topMenu.populateElement())
            .on('contextmenu', function (event) {
                event.preventDefault();
                topMenu.open();
            });

        $(document).on('click', function () {
            topMenu.close();
        });

        return $.Deferred().resolve().promise();
    };
});

}(RequireJS.define));
