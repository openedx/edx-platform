(function () {
    'use strict';
    describe('Video Context Menu', function () {
        var state, openMenu, keyPressEvent, openSubmenuMouse, openSubmenuKeyboard, closeSubmenuMouse,
            closeSubmenuKeyboard, menu, menuItems, menuSubmenuItem, submenu, submenuItems, overlay, playButton;

        openMenu = function () {
            var container = $('.video');
            jasmine.Clock.useMock();
            container.find('video').trigger('contextmenu');
            menu = container.children('.contextmenu');
            menuItems = menu.children('.menu-item').not('.submenu-item');
            menuSubmenuItem = menu.children('.menu-item.submenu-item');
            submenu = menuSubmenuItem.children('.submenu');
            submenuItems = submenu.children('.menu-item');
            overlay = container.children('.overlay');
            playButton = $('.video_control.play');
        };

        keyPressEvent = function(key) {
            return $.Event('keydown', {keyCode: key});
        };

        openSubmenuMouse = function (menuSubmenuItem) {
            menuSubmenuItem.mouseover();
            jasmine.Clock.tick(200);
            expect(menuSubmenuItem).toHaveClass('is-opened');
        };

        openSubmenuKeyboard = function (menuSubmenuItem, keyCode) {
            menuSubmenuItem.focus().trigger(keyPressEvent(keyCode || $.ui.keyCode.RIGHT));
            expect(menuSubmenuItem).toHaveClass('is-opened');
            expect(menuSubmenuItem.children().first()).toBeFocused();
        };

        closeSubmenuMouse = function (menuSubmenuItem) {
            menuSubmenuItem.mouseleave();
            jasmine.Clock.tick(200);
            expect(menuSubmenuItem).not.toHaveClass('is-opened');
        };

        closeSubmenuKeyboard = function (menuSubmenuItem) {
            menuSubmenuItem.children().first().focus().trigger(keyPressEvent($.ui.keyCode.LEFT));
            expect(menuSubmenuItem).not.toHaveClass('is-opened');
            expect(menuSubmenuItem).toBeFocused();
        };

        beforeEach(function () {
            // $.cookie is mocked, make sure we have a state with an unmuted volume.
            $.cookie.andReturn('100');
            this.addMatchers({
                toBeFocused: function () {
                    return {
                        compare: function (actual) {
                            return { pass: $(actual)[0] === $(actual)[0].ownerDocument.activeElement };
                        }
                    };
                },
                toHaveCorrectLabels: function (labelsList) {
                    return _.difference(labelsList, _.map(this.actual, function (item) {
                        return $(item).text();
                    })).length === 0;
                }
            });
        });

        afterEach(function () {
            $('source').remove();
            _.result(state.storage, 'clear');
            _.result($('video').data('contextmenu'), 'destroy');
            _.result(state.videoPlayer, 'destroy');
        });

        describe('constructor', function () {
            it('the structure should be created on first `contextmenu` call', function () {
                state = jasmine.initializePlayer();
                expect(menu).not.toExist();
                openMenu();
                /*
                  Make sure we have the expected HTML structure:
                   - Play (Pause)
                   - Mute (Unmute)
                   - Fill browser (Exit full browser)
                   - Speed >
                             - 0.75x
                             - 1.0x
                             - 1.25x
                             - 1.50x
                */

                // Only one context menu per video container
                expect(menu).toExist();
                expect(menu).toHaveClass('is-opened');
                expect(menuItems).toHaveCorrectLabels(['Play', 'Mute', 'Fill browser']);
                expect(menuSubmenuItem.children('span')).toHaveText('Speed');
                expect(submenuItems).toHaveCorrectLabels(['0.75x', '1.0x', '1.25x', '1.50x']);
                // Check that one of the speed submenu item is selected
                expect(_.size(submenuItems.filter('.is-selected'))).toBe(1);
            });

            it('add ARIA attributes to menu, menu items, submenu and submenu items', function () {
                state = jasmine.initializePlayer();
                openMenu();
                // Menu and its items.
                expect(menu).toHaveAttr('role', 'menu');
                menuItems.each(function () {
                    expect($(this)).toHaveAttrs({
                        'aria-selected': 'false',
                        'role': 'menuitem'
                    });
                });

                expect(menuSubmenuItem).toHaveAttrs({
                    'aria-expanded': 'false',
                    'aria-haspopup': 'true',
                    'role': 'menuitem'
                });

                // Submenu and its items.
                expect(submenu).toHaveAttr('role', 'menu');
                submenuItems.each(function () {
                    expect($(this)).toHaveAttr('role', 'menuitem');
                    expect($(this)).toHaveAttr('aria-selected');
                });
            });

            it('is not used by Youtube type of video player', function () {
                state = jasmine.initializePlayer('video.html');
                expect($('video, iframe')).not.toHaveData('contextmenu');
            });
        });

        describe('methods:', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
                openMenu();
            });

            it('menu can be destroyed successfully', function () {
                var menuitemEvents = ['click', 'keydown', 'contextmenu', 'mouseover'],
                    menuEvents = ['keydown', 'contextmenu', 'mouseleave', 'mouseover'];

                menu.data('menu').destroy();
                expect(menu).not.toExist();
                expect(overlay).not.toExist();
                _.each(menuitemEvents, function (eventName) {
                    expect(menuItems.first()).not.toHandle(eventName);
                })
                _.each(menuEvents, function (eventName) {
                    expect(menuSubmenuItem).not.toHandle(eventName);
                })
                _.each(menuEvents, function (eventName) {
                    expect(menu).not.toHandle(eventName);
                })
                expect($('video')).not.toHandle('contextmenu');
                expect($('video')).not.toHaveData('contextmenu');
            });

            it('can change label for the submenu', function () {
                expect(menuSubmenuItem.children('span')).toHaveText('Speed');
                menuSubmenuItem.data('menu').setLabel('New Name');
                expect(menuSubmenuItem.children('span')).toHaveText('New Name');
            });

            it('can change label for the menuitem', function () {
                expect(menuItems.first()).toHaveText('Play');
                menuItems.first().data('menu').setLabel('Pause');
                expect(menuItems.first()).toHaveText('Pause');
            });
        });

        describe('when video is right-clicked', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
                openMenu();
            });

            it('context menu opens', function () {
                expect(menu).toHaveClass('is-opened');
                expect(overlay).toExist();
            });

            it('mouseover and mouseleave behave as expected', function () {
                openSubmenuMouse(menuSubmenuItem);
                expect(menuSubmenuItem).toHaveClass('is-opened');
                closeSubmenuMouse(menuSubmenuItem);
                expect(menuSubmenuItem).not.toHaveClass('is-opened');
                submenuItems.eq(1).mouseover();
                expect(submenuItems.eq(1)).toBeFocused();
            });

            it('mouse left-clicking outside of the context menu will close it', function () {
                // Left-click outside of open menu, for example on Play button
                playButton.click();
                expect(menu).not.toHaveClass('is-opened');
                expect(overlay).not.toExist();
            });

            it('mouse right-clicking outside of video will close it', function () {
                // Right-click outside of open menu for example on Play button
                playButton.trigger('contextmenu');
                expect(menu).not.toHaveClass('is-opened');
                expect(overlay).not.toExist();
            });

            it('mouse right-clicking inside video but outside of context menu will not close it', function () {
                spyOn(menu.data('menu'), 'pointInContainerBox').andReturn(true);
                overlay.trigger('contextmenu');
                expect(menu).toHaveClass('is-opened');
                expect(overlay).toExist();
            });

            it('mouse right-clicking inside video but outside of context menu will close submenus', function () {
                spyOn(menu.data('menu'), 'pointInContainerBox').andReturn(true);
                openSubmenuMouse(menuSubmenuItem);
                expect(menuSubmenuItem).toHaveClass('is-opened');
                overlay.trigger('contextmenu');
                expect(menuSubmenuItem).not.toHaveClass('is-opened');
            });

            it('mouse left/right-clicking behaves as expected on play/pause menu item', function () {
                var menuItem = menuItems.first();
                spyOn(state.videoPlayer, 'isPlaying');
                spyOn(state.videoPlayer, 'play').andCallFake(function () {
                    state.videoPlayer.isPlaying.andReturn(true);
                    state.el.trigger('play');
                });
                spyOn(state.videoPlayer, 'pause').andCallFake(function () {
                    state.videoPlayer.isPlaying.andReturn(false);
                    state.el.trigger('pause');
                });
                // Left-click on play
                menuItem.click();
                expect(state.videoPlayer.play).toHaveBeenCalled();
                expect(menuItem).toHaveText('Pause');
                openMenu();
                // Left-click on pause
                menuItem.click();
                expect(state.videoPlayer.pause).toHaveBeenCalled();
                expect(menuItem).toHaveText('Play');
                state.videoPlayer.play.reset();
                // Right-click on play
                menuItem.trigger('contextmenu');
                expect(state.videoPlayer.play).toHaveBeenCalled();
                expect(menuItem).toHaveText('Pause');
            });

            it('mouse left/right-clicking behaves as expected on mute/unmute menu item', function () {
                var menuItem = menuItems.eq(1);
                // Left-click on mute
                menuItem.click();
                expect(state.videoVolumeControl.getMuteStatus()).toBe(true);
                expect(menuItem).toHaveText('Unmute');
                openMenu();
                // Left-click on unmute
                menuItem.click();
                expect(state.videoVolumeControl.getMuteStatus()).toBe(false);
                expect(menuItem).toHaveText('Mute');
                // Right-click on mute
                menuItem.trigger('contextmenu');
                expect(state.videoVolumeControl.getMuteStatus()).toBe(true);
                expect(menuItem).toHaveText('Unmute');
                openMenu();
                // Right-click on unmute
                menuItem.trigger('contextmenu');
                expect(state.videoVolumeControl.getMuteStatus()).toBe(false);
                expect(menuItem).toHaveText('Mute');
            });

            it('mouse left/right-clicking behaves as expected on go to Exit full browser menu item', function () {
                var menuItem = menuItems.eq(2);
                // Left-click on Fill browser
                menuItem.click();
                expect(state.isFullScreen).toBe(true);
                expect(menuItem).toHaveText('Exit full browser');
                openMenu();
                // Left-click on Exit full browser
                menuItem.click();
                expect(state.isFullScreen).toBe(false);
                expect(menuItem).toHaveText('Fill browser');
                // Right-click on Fill browser
                menuItem.trigger('contextmenu');
                expect(state.isFullScreen).toBe(true);
                expect(menuItem).toHaveText('Exit full browser');
                openMenu();
                // Right-click on Exit full browser
                menuItem.trigger('contextmenu');
                expect(state.isFullScreen).toBe(false);
                expect(menuItem).toHaveText('Fill browser');
            });

            it('mouse left/right-clicking behaves as expected on speed submenu item', function () {
                // Set speed to 0.75x
                state.videoSpeedControl.setSpeed('0.75');
                // Left-click on second submenu speed (1.0x)
                openSubmenuMouse(menuSubmenuItem);
                submenuItems.eq(1).click();

                // Expect speed to be 1.0x
                expect(state.videoSpeedControl.currentSpeed).toBe('1.0');
                // Expect speed submenu item 0.75x not to be active
                expect(submenuItems.first()).not.toHaveClass('is-selected');
                // Expect speed submenu item 1.0x to be active
                expect(submenuItems.eq(1)).toHaveClass('is-selected');

                // Set speed to 0.75x
                state.videoSpeedControl.setSpeed('0.75');
                // Right-click on second submenu speed (1.0x)
                openSubmenuMouse(menuSubmenuItem);
                submenuItems.eq(1).trigger('contextmenu');

                // Expect speed to be 1.0x
                expect(state.videoSpeedControl.currentSpeed).toBe('1.0');
                // Expect speed submenu item 0.75x not to be active
                expect(submenuItems.first()).not.toHaveClass('is-selected');
                // Expect speed submenu item 1.0x to be active
                expect(submenuItems.eq(1)).toHaveClass('is-selected');
            });
        });

        describe('Keyboard interactions', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
                openMenu();
            });

            it('focus the first item of the just opened menu on UP keydown', function () {
                menu.trigger(keyPressEvent($.ui.keyCode.UP));
                expect(menuSubmenuItem).toBeFocused();
            });

            it('focus the last item of the just opened menu on DOWN keydown', function () {
                menu.trigger(keyPressEvent($.ui.keyCode.DOWN));
                expect(menuItems.first()).toBeFocused();
            });

            it('open the submenu on ENTER keydown', function () {
                openSubmenuKeyboard(menuSubmenuItem, $.ui.keyCode.ENTER);
                expect(menuSubmenuItem).toHaveClass('is-opened');
                expect(submenuItems.first()).toBeFocused();
            });

            it('open the submenu on SPACE keydown', function () {
                openSubmenuKeyboard(menuSubmenuItem, $.ui.keyCode.SPACE);
                expect(menuSubmenuItem).toHaveClass('is-opened');
                expect(submenuItems.first()).toBeFocused();
            });

            it('open the submenu on RIGHT keydown', function () {
                openSubmenuKeyboard(menuSubmenuItem, $.ui.keyCode.RIGHT);
                expect(menuSubmenuItem).toHaveClass('is-opened');
                expect(submenuItems.first()).toBeFocused();
            });

            it('close the menu on ESCAPE keydown', function () {
                menu.trigger(keyPressEvent($.ui.keyCode.ESCAPE));
                expect(menu).not.toHaveClass('is-opened');
                expect(overlay).not.toExist();
            });

            it('close the submenu on ESCAPE keydown', function () {
                openSubmenuKeyboard(menuSubmenuItem);
                menuSubmenuItem.trigger(keyPressEvent($.ui.keyCode.ESCAPE));
                expect(menuSubmenuItem).not.toHaveClass('is-opened');
                expect(overlay).not.toExist();
            });

            it('close the submenu on LEFT keydown on submenu items', function () {
                closeSubmenuKeyboard(menuSubmenuItem);
            });

            it('do nothing on RIGHT keydown on submenu item', function () {
                submenuItems.eq(1).focus().trigger(keyPressEvent($.ui.keyCode.RIGHT)); // Mute
                // Is still focused.
                expect(submenuItems.eq(1)).toBeFocused();
            });

            it('do nothing on TAB keydown on menu item', function () {
                submenuItems.eq(1).focus().trigger(keyPressEvent($.ui.keyCode.TAB)); // Mute
                // Is still focused.
                expect(submenuItems.eq(1)).toBeFocused();
            });

            it('UP and DOWN keydown function as expected on menu/submenu items', function () {
                menuItems.eq(0).focus(); // Play
                expect(menuItems.eq(0)).toBeFocused();
                menuItems.eq(0).trigger(keyPressEvent($.ui.keyCode.DOWN));
                expect(menuItems.eq(1)).toBeFocused(); // Mute
                menuItems.eq(1).trigger(keyPressEvent($.ui.keyCode.DOWN));
                expect(menuItems.eq(2)).toBeFocused(); // Fullscreen
                menuItems.eq(2).trigger(keyPressEvent($.ui.keyCode.DOWN));
                expect(menuSubmenuItem).toBeFocused(); // Speed
                menuSubmenuItem.trigger(keyPressEvent($.ui.keyCode.DOWN));
                expect(menuItems.eq(0)).toBeFocused(); // Play

                menuItems.eq(0).trigger(keyPressEvent($.ui.keyCode.UP));
                expect(menuSubmenuItem).toBeFocused(); // Speed
                menuSubmenuItem.trigger(keyPressEvent($.ui.keyCode.UP));
                // Check if hidden item can be skipped correctly.
                menuItems.eq(2).hide(); // hide Fullscreen item
                expect(menuItems.eq(1)).toBeFocused(); // Mute
                menuItems.eq(1).trigger(keyPressEvent($.ui.keyCode.UP));
                expect(menuItems.eq(0)).toBeFocused(); // Play
            });

            it('current item is still focused if all siblings are hidden', function () {
                menuItems.eq(0).focus(); // Play
                expect(menuItems.eq(0)).toBeFocused(); // hide all siblings
                menuItems.eq(0).siblings().hide();
                menuSubmenuItem.trigger(keyPressEvent($.ui.keyCode.DOWN));
                expect(menuItems.eq(0)).toBeFocused();
                menuSubmenuItem.trigger(keyPressEvent($.ui.keyCode.UP));
                expect(menuItems.eq(0)).toBeFocused();
            });

            it('ENTER keydown on menu/submenu item selects its data and closes menu', function () {
                menuItems.eq(2).focus().trigger(keyPressEvent($.ui.keyCode.ENTER)); // Fullscreen
                expect(menuItems.eq(2)).toHaveClass('is-selected');
                expect(menuItems.eq(2).siblings()).not.toHaveClass('is-selected');
                expect(state.isFullScreen).toBeTruthy();
                expect(menuItems.eq(2)).toHaveText('Exit full browser');
            });

            it('SPACE keydown on menu/submenu item selects its data and closes menu', function () {
                submenuItems.eq(2).focus().trigger(keyPressEvent($.ui.keyCode.SPACE)); // 1.25x
                expect(submenuItems.eq(2)).toHaveClass('is-selected');
                expect(submenuItems.eq(2).siblings()).not.toHaveClass('is-selected');
                expect(state.videoSpeedControl.currentSpeed).toBe('1.25');
            });
        });
    });
})();
