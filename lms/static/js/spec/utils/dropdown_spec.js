define([
    'jquery', 'logger'
], function($, Logger) {
    'use strict';

    describe('Dropdown Menus', function() {

        describe('always', function() {
            var wrapper, button, menu, menu_item, menu_action;

            beforeEach(function() {
                loadFixtures('js/fixtures/utils/dropdown.html');
                wrapper = $('.wrapper-more-actions');
                button = wrapper.children('.button-more.has-dropdown');
                menu = wrapper.children('.dropdown-menu');
                menu_item = menu.children('.dropdown-item');
                menu_action = menu_item.children('.action');
                spyOn($.fn, 'focus').andCallThrough();
            });

            it('adds the dropdown menus', function() {
                expect(button.length).toBe(1);
                expect(wrapper.length).toBe(button.length);
                expect(menu.length).toBe(wrapper.length);
                expect(menu_item.length).toBeGreaterThan(0);
                expect(menu_action.length).toBe(menu_item.length);
            });

            it('ensures ARIA attributes are present on button and menu', function() {
                expect(button).toHaveAttr({
                    'aria-haspopup': 'true',
                    'aria-expanded': 'false',
                    'aria-controls': 'dropdown'
                });

                expect(menu).toHaveAttr({
                    'tabindex': '-1'
                });
            });
        });

        describe('when running', function() {
            function keyPressEvent(key) {
                return $.Event('keydown', { keyCode: key });
            }

            var wrapper, button, menu, menu_item, menu_action, KEY = $.ui.keyCode,

            it('opens the menu on button click', function() {
                button.click();
                expect(button).toHaveClass('is-active');
                expect(button).toHaveAttr({
                    'aria-expanded': 'true'
                });
                expect(menu).toHaveClass('is-visible');
            });

            it('closes the menu on outside click', function() {
                $(window).click();
                expect(button).not.toHaveClass('is-active');
                expect(button).toHaveAttr({
                    'aria-expanded': 'false'
                });
                expect(menu).not.toHaveClass('is-visible');
                expect(menu).toHaveClass('is-hidden');
            });

            it('opens the menu on ENTER kepress', function() {
                button.trigger(keyPressEvent(KEY.ENTER));
                expect(button).toHaveClass('is-active');
                expect(button).toHaveAttr({
                    'aria-expanded': 'true'
                });
                expect(menu).toHaveClass('is-visible');
                expect(menu.focus).toHaveBeenCalled();
            });

            it('opens the menu on DOWN keypress', function() {
                button.trigger(keyPressEvent(KEY.DOWN));
                expect(button).toHaveClass('is-active');
                expect(button).toHaveAttr({
                    'aria-expanded': 'true'
                });
                expect(menu).toHaveClass('is-visible');
                expect(menu.focus).toHaveBeenCalled();
            });

            it('moves between menu items on UP or DOWN', function() {
                var last_item = menu_item.length - 1, i;
                container.trigger(keyPressEvent(KEY.ENTER));

                for (i = last_item; i >= 0; i--) {
                    menu_item.eq(i).trigger(keyPressEvent(KEY.UP));
                }

                for (i = 0; i <= last_item; i++) {
                    menu_item.eq(i).trigger(keyPressEvent(KEY.DOWN));
                }
            });

            it('opens the menu on SPACE kepress', function() {
                button.trigger(keyPressEvent(KEY.SPACE));
                expect(button).toHaveClass('is-active');
                expect(button).toHaveAttr({
                    'aria-expanded': 'true'
                });
                expect(menu).toHaveClass('is-visible');
                expect(menu.focus).toHaveBeenCalled();
            });

            it('closes the menu on ESC keypress', function() {
                $(window).trigger(keyPressEvent(KEY.ESC));
                expect(button).not.toHaveClass('is-active');
                expect(button).toHaveAttr({
                    'aria-expanded': 'false'
                });
                expect(menu).not.toHaveClass('is-visible');
                expect(menu).toHaveClass('is-hidden');
            });
        });
    });
}).call(this);