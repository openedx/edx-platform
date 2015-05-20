define(['jquery', 'js/utils/dropdown'], function($) {
    'use strict';

    describe('Dropdown Menus', function() {
        var wrapper, button, menu, menu_item, menu_action;

        beforeEach(function() {
            loadFixtures('js/fixtures/utils/dropdown.html');
            wrapper = $('.wrapper-more-actions');
            button = wrapper.children('.button-more.has-dropdown');
            menu = wrapper.children('.dropdown-menu');
            menu_item = menu.children('.dropdown-item');
            menu_action = menu_item.children('.action');
            spyOn($.fn, 'focus').andCallThrough();
            edx.util.dropdown.init();
        });

        describe('always', function() {

            it('adds the dropdown menus', function() {
                expect(wrapper.length).toBe(button.length);
                expect(button.length).toBe(1);
                expect(menu.length).toBe(wrapper.length);
                expect(menu_item.length).toBeGreaterThan(1);
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

            it('opens the menu on button click', function() {
                // console.log(button.length);
                button.focus();
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
                button.focus();
                button.trigger(keyPressEvent(13)); // Enter
                expect(button).toHaveClass('is-active');
                expect(button).toHaveAttr({
                    'aria-expanded': 'true'
                });
                expect(menu).toHaveClass('is-visible');
                expect(menu.focus).toHaveBeenCalled();
            });

            it('opens the menu on DOWN keypress', function() {
                button.focus();
                button.trigger(keyPressEvent(40)); // Down arrow
                expect(button).toHaveClass('is-active');
                expect(button).toHaveAttr({
                    'aria-expanded': 'true'
                });
                expect(menu).toHaveClass('is-visible');
                expect(menu.focus).toHaveBeenCalled();
            });

            it('focuses on the first item after menu is opened', function() {
                button.focus();
                button.trigger(keyPressEvent(40)); // Down arrow
                expect(menu.focus).toHaveBeenCalled();
                menu.trigger(keyPressEvent(40)); // Down arrow
                expect(menu_item.eq(0).focus).toHaveBeenCalled();
            });

            it('moves between menu items on UP or DOWN', function() {
                var last_item = menu_item.length - 1, i;
                menu.focus();
                menu.trigger(keyPressEvent(13)); // Enter

                for (i = last_item; i >= 0; i--) {
                    menu_item.eq(i).trigger(keyPressEvent(38)); // Up arrow
                    expect(menu_item.eq(i).focus).toHaveBeenCalled();
                }

                for (i = 0; i <= last_item; i++) {
                    menu_item.eq(i).trigger(keyPressEvent(40)); // Down arrow
                    expect(menu_item.eq(i).focus).toHaveBeenCalled();
                }
            });

            it('closes the menu on ESC keypress', function() {
                $(window).trigger(keyPressEvent(49)); // Esc
                expect(button).not.toHaveClass('is-active');
                expect(button).toHaveAttr({
                    'aria-expanded': 'false'
                });
                expect(menu).not.toHaveClass('is-visible');
                expect(menu).toHaveClass('is-hidden');
            });
        });
    });
});