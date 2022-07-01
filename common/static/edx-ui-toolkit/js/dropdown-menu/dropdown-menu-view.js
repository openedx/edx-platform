/**
 * A Backbone view that renders a fully accessible dropdown menu.
 *
 * Initialize the view by passing in the following attributes:
 *
 *~~~ javascript
 * view = new DropdownMenuView({
 *     className: 'space separated string of classes for element',
 *     model: new Backbone.Model({
 *         main: {
 *             image: 'http://placehold.it/40x40',
 *             screenreader_label: 'Dashboard for: ',
 *             text: 'username',
 *             url: 'dashboard'
 *         },
 *         button: {
 *             icon: 'icon-angle-down',
 *             label: 'User options dropdown'
 *         },
 *         items: [
 *             {
 *                 text: 'Account',
 *                 url: 'account_settings'
 *             }, {
 *                 text: 'Sign Out',
 *                 url: 'logout'
 *             }
 *         ]
 *     }),
 *     parent: 'selector for parent element that will be replaced with dropdown menu',
 *     ...
 * });
 *~~~
 * @module DropdownMenuView
 */
(function(define) {
    'use strict';

    define([
        'backbone',
        'jquery',
        'underscore',
        'edx-ui-toolkit/js/utils/constants',
        'text!./dropdown.underscore'
    ],
        function(Backbone, $, _, constants, DropdownTpl) {
            var DropdownMenuView = Backbone.View.extend({
                tpl: _.template(DropdownTpl),

                events: {
                    'click .js-dropdown-button': 'clickOpenDropdown',
                    'click a': 'analyticsLinkClick',
                    keydown: 'viewKeypress'
                },

                dropdownButton: '.js-dropdown-button',

                menu: '.dropdown-menu',

                initialize: function(options) {
                    if (options.parent) {
                        this.$parent = $(options.parent);
                    }

                    this.menuId = options.menuId || 'dropdown-menu-' + this.cid;
                    this.keyBack = [constants.keyCodes.up, constants.keyCodes.left];
                    this.keyForward = [constants.keyCodes.down, constants.keyCodes.right];
                    this.keyClose = [constants.keyCodes.esc, constants.keyCodes.space];
                },

                className: function() {
                    return this.options.className;
                },

                render: function() {
                    /**
                     * Set in the render function to prevent error when
                     * view is used with a pre-rendered DOM
                     */
                    this.model.set({menuId: this.menuId});

                    this.$el.html(this.tpl(this.model.toJSON()));
                    this.$parent.replaceWith(this.$el);
                    this.postRender();

                    return this;
                },

                postRender: function() {
                    this.$menu = this.$('.dropdown-menu');
                    this.$page = $(document);
                    this.$dropdownButton = this.$(this.dropdownButton);
                    this.$lastItem = this.$menu.find('li:last-child a');
                },

                /**
                 * Function to track analytics.
                 *
                 * By default it doesn't do anything, to utilize please
                 * extend the View and implement a method such as the
                 * following:
                 *
                 *~~~ javascript
                 * var $link = $(event.target),
                 *     label = $link.hasClass('menu-title') ? 'Dashboard' : $link.html().trim();
                 *
                 * window.analytics.track('user_dropdown.clicked', {
                 *     category: 'navigation',
                 *     label: label,
                 *     link: $link.attr('href')
                 * });
                 *~~~
                 *
                 * @param {object} event The event to be tracked.
                 * @returns {*} The event.
                 */
                analyticsLinkClick: function(event) {
                    return event;
                },

                clickCloseDropdown: function(event, context) {
                    var $el = $(event.target) || $(document),
                        $btn;

                    // When using edX Pattern Library icons the target
                    // is sometimes not the button.
                    if (!$el.hasClass(this.dropdownButton)) {
                        // If there is a parent dropdown button that is the element to test
                        $btn = $el.closest(this.dropdownButton);
                        if ($btn.length > 0) {
                            $el = $btn;
                        }
                    }

                    if (!$el.hasClass('button-more') && !$el.hasClass('has-dropdown')) {
                        context.closeDropdownMenu();
                    }
                },

                clickOpenDropdown: function(event) {
                    event.preventDefault();
                    this.openMenu(this.$dropdownButton);
                },

                closeDropdownMenu: function() {
                    var $open = this.$(this.menu);

                    $open.removeClass('is-visible')
                        .addClass('is-hidden');

                    this.$dropdownButton
                        .removeClass('is-active')
                        .attr('aria-expanded', 'false');
                },

                focusFirstItem: function() {
                    this.$menu.find('.dropdown-item:first-child .action').focus();
                },

                focusLastItem: function() {
                    this.$lastItem.focus();
                },

                handlerIsAction: function(key, $el) {
                    if (_.contains(this.keyForward, key)) {
                        this.nextMenuItemLink($el);
                    } else if (_.contains(this.keyBack, key)) {
                        this.previousMenuItemLink($el);
                    }
                },

                handlerIsButton: function(key, event) {
                    if (_.contains(this.keyForward, key)) {
                        this.focusFirstItem();
                        // if up arrow or left arrow key pressed or shift+tab
                    } else if (_.contains(this.keyBack, key) || (key === constants.keyCodes.tab && event.shiftKey)) {
                        event.preventDefault();
                        this.focusLastItem();
                    }
                },

                handlerIsMenu: function(key) {
                    if (_.contains(this.keyForward, key)) {
                        this.focusFirstItem();
                    } else if (_.contains(this.keyBack, key)) {
                        this.$dropdownButton.focus();
                    }
                },

                handlerPageClicks: function(context) {
                    // Only want 1 event listener for click.dropdown
                    // on the page so unbind for instantiating
                    this.$page.off('click.dropdown');
                    this.$page.on('click.dropdown', function(event) {
                        context.clickCloseDropdown(event, context);
                    });
                },

                nextMenuItemLink: function($el) {
                    var items = this.$('.dropdown-menu').children('.dropdown-item').find('.action'),
                        itemsCount = items.length - 1,
                        index = items.index($el),
                        next = index + 1;

                    if (index === itemsCount) {
                        this.$dropdownButton.focus();
                    } else {
                        items.eq(next).focus();
                    }
                },

                openMenu: function($btn) {
                    var $menu = this.$menu;
                    if ($menu.hasClass('is-visible')) {
                        this.closeDropdownMenu();
                    } else {
                        $btn.addClass('is-active')
                            .attr('aria-expanded', 'true');

                        $menu.removeClass('is-hidden')
                            .addClass('is-visible');

                        $menu.focus();
                        this.setOrientation();
                        this.handlerPageClicks(this);
                    }
                },

                previousMenuItemLink: function($el) {
                    var items = this.$('.dropdown-menu').children('.dropdown-item').find('.action'),
                        index = items.index($el),
                        prev = index - 1;

                    if (index === 0) {
                        this.$dropdownButton.focus();
                    } else {
                        items.eq(prev).focus();
                    }
                },

                setOrientation: function() {
                    var midpoint = $(window).width() / 2,
                        alignClass = (this.$dropdownButton.offset().left > midpoint) ? 'align-right' : 'align-left';

                    this.$menu
                        .removeClass('align-left align-right')
                        .addClass(alignClass);
                },

                viewKeypress: function(event) {
                    var key = event.keyCode,
                        $el = $(event.target);

                    if (_.contains(this.keyForward, key) || _.contains(this.keyBack, key)) {
                        // Prevent default behavior if one of our trigger keys
                        event.preventDefault();
                    }

                    if (key === constants.keyCodes.tab && !event.shiftKey && _.first($el) === _.first(this.$lastItem)) {
                        event.preventDefault();
                        this.$dropdownButton.focus();
                    } else if (_.contains(this.keyClose, key)) {
                        this.closeDropdownMenu();
                        this.$dropdownButton.focus();
                    } else if ($el.hasClass('action')) {
                        // Key handlers for when a menu item has focus
                        this.handlerIsAction(key, $el);
                    } else if ($el.hasClass('dropdown-menu')) {
                        // Key handlers for when the menu itself has focus, before an item within it receives focus
                        this.handlerIsMenu(key);
                    } else if ($el.hasClass('has-dropdown')) {
                        // Key handlers for when the button that opens the menu has focus
                        this.handlerIsButton(key, event);
                    }
                }
            });

            return DropdownMenuView;
        }
    );
}).call(
    this,
    // Use the default 'define' function if available, else use 'RequireJS.define'
    typeof define === 'function' && define.amd ? define : RequireJS.define
);
