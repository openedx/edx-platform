(function (undefined) {
    describe('Video Accessible Menu', function () {
        var state;

        afterEach(function () {
            $('source').remove();
            state.storage.clear();
            state.videoPlayer.destroy();
        });

        describe('constructor', function () {
            describe('always', function () {
                var videoTracks, container, button, menu, menuItems,
                    menuItemsLinks;

                beforeEach(function () {
                    state = jasmine.initializePlayer();
                    videoTracks = $('li.video-tracks');
                    container = videoTracks.children('div.a11y-menu-container');
                    button = container.children('a.a11y-menu-button');
                    menuList = container.children('ol.a11y-menu-list');
                    menuItems = menuList.children('li.a11y-menu-item');
                    menuItemsLinks = menuItems.children('a.a11y-menu-item-link');
                });

                it('add the accessible menu', function () {
                    var activeMenuItem;
                    // Make sure we have the expected HTML structure:
                    // Menu container exists
                    expect(container.length).toBe(1);
                    // Only one button and one menu list per menu container.
                    expect(button.length).toBe(1);
                    expect(menuList.length).toBe(1);
                    // At least one menu item and one menu link per menu
                    // container. Exact length test?
                    expect(menuItems.length).toBeGreaterThan(0);
                    expect(menuItemsLinks.length).toBeGreaterThan(0);
                    expect(menuItems.length).toBe(menuItemsLinks.length);
                    // And one menu item is active
                    activeMenuItem = menuItems.filter('.active');
                    expect(activeMenuItem.length).toBe(1);

                    expect(activeMenuItem.children('a.a11y-menu-item-link'))
                        .toHaveData('value', 'srt');

                    expect(activeMenuItem.children('a.a11y-menu-item-link'))
                        .toHaveHtml('SubRip (.srt) file');

                    /* TO DO: Check that all the anchors contain correct text.
                    $.each(li.toArray().reverse(), function (index, link) {
                        expect($(link)).toHaveData(
                            'speed', state.videoSpeedControl.speeds[index]
                        );
                        expect($(link).find('a').text()).toBe(
                            state.videoSpeedControl.speeds[index] + 'x'
                        );
                    });
                    */
                });
            });

            describe('when running', function () {
                var videoTracks, container, button, menu, menuItems,
                    menuItemsLinks, KEY = $.ui.keyCode,

                    keyPressEvent = function(key) {
                        return $.Event('keydown', {keyCode: key});
                    },

                    tabBackPressEvent = function() {
                        return $.Event('keydown',
                                       {keyCode: KEY.TAB, shiftKey: true});
                    },

                    tabForwardPressEvent = function() {
                        return $.Event('keydown',
                                       {keyCode: KEY.TAB, shiftKey: false});
                    },

                    // Get previous element in array or cyles back to the last
                    // if it is the first.
                    previousSpeed = function(index) {
                        return speedEntries.eq(index < 1 ?
                                               speedEntries.length - 1 :
                                               index - 1);
                    },

                    // Get next element in array or cyles back to the first if
                    // it is the last.
                    nextSpeed = function(index) {
                        return speedEntries.eq(index >= speedEntries.length-1 ?
                                               0 :
                                               index + 1);
                    };

                beforeEach(function () {
                    state = jasmine.initializePlayer();
                    videoTracks = $('li.video-tracks');
                    container = videoTracks.children('div.a11y-menu-container');
                    button = container.children('a.a11y-menu-button');
                    menuList = container.children('ol.a11y-menu-list');
                    menuItems = menuList.children('li.a11y-menu-item');
                    menuItemsLinks = menuItems.children('a.a11y-menu-item-link');
                    spyOn($.fn, 'focus').and.callThrough();
                });

                it('open/close the menu on mouseenter/mouseleave', function () {
                    container.mouseenter();
                    expect(container).toHaveClass('open');
                    container.mouseleave();
                    expect(container).not.toHaveClass('open');
                });

                it('do not close the menu on mouseleave if a menu item has ' +
                    'focus', function () {
                    // Open menu. Focus is on last menu item.
                    container.trigger(keyPressEvent(KEY.ENTER));
                    container.mouseenter().mouseleave();
                    expect(container).toHaveClass('open');
                });

                it('close the menu on click', function () {
                    container.mouseenter().click();
                    expect(container).not.toHaveClass('open');
                });

                it('close the menu on outside click', function () {
                    container.trigger(keyPressEvent(KEY.ENTER));
                    $(window).click();
                    expect(container).not.toHaveClass('open');
                });

                it('open the menu on ENTER keydown', function () {
                    container.trigger(keyPressEvent(KEY.ENTER));
                    expect(container).toHaveClass('open');
                    expect(menuItemsLinks.last().focus).toHaveBeenCalled();
                });

                it('open the menu on SPACE keydown', function () {
                    container.trigger(keyPressEvent(KEY.SPACE));
                    expect(container).toHaveClass('open');
                    expect(menuItemsLinks.last().focus).toHaveBeenCalled();
                });

                it('open the menu on UP keydown', function () {
                    container.trigger(keyPressEvent(KEY.UP));
                    expect(container).toHaveClass('open');
                    expect(menuItemsLinks.last().focus).toHaveBeenCalled();
                });

                it('close the menu on ESCAPE keydown', function () {
                    container.trigger(keyPressEvent(KEY.ESCAPE));
                    expect(container).not.toHaveClass('open');
                });

                it('UP and DOWN keydown function as expected on menu items',
                   function () {
                    // Iterate through list in both directions and check if
                    // things wrap up correctly.
                    var lastEntry = menuItemsLinks.length-1, i;

                    // First open menu
                    container.trigger(keyPressEvent(KEY.UP));

                    // Iterate with UP key until we have looped.
                    for (i = lastEntry; i >= 0; i--) {
                        menuItemsLinks.eq(i).trigger(keyPressEvent(KEY.UP));
                    }

                    // Iterate with DOWN key until we have looped.
                    for (i = 0; i <= lastEntry; i++) {
                        menuItemsLinks.eq(i).trigger(keyPressEvent(KEY.DOWN));
                    }

                    // Test if each element has been called twice.
                    expect($.fn.focus.calls.count())
                        .toEqual(2*menuItemsLinks.length+1);
                });

                it('ESC keydown on menu item closes menu', function () {
                    // First open menu. Focus is on last speed entry.
                    container.trigger(keyPressEvent(KEY.UP));
                    menuItemsLinks.last().trigger(keyPressEvent(KEY.ESCAPE));

                    // Menu is closed and focus has been returned to speed
                    // control.
                    expect(container).not.toHaveClass('open');
                    expect(container.focus).toHaveBeenCalled();
                });

                it('ENTER keydown on menu item selects its data and closes menu',
                   function () {
                    // First open menu.
                    container.trigger(keyPressEvent(KEY.UP));
                    // Focus on '.txt'
                    menuItemsLinks.eq(0).focus();
                    menuItemsLinks.eq(0).trigger(keyPressEvent(KEY.ENTER));

                    // Menu is closed, focus has been returned to container
                    // and file format is '.txt'.
                    /* TO DO
                    expect(container.focus).toHaveBeenCalled();
                    expect($('.video_speeds li[data-speed="1.50"]'))
                        .toHaveClass('active');
                    expect($('.speeds p.active')).toHaveHtml('1.50x');
                    */
                });

                it('SPACE keydown on menu item selects its data and closes menu',
                   function () {
                    // First open menu.
                    container.trigger(keyPressEvent(KEY.UP));
                    // Focus on '.txt'
                    menuItemsLinks.eq(0).focus();
                    menuItemsLinks.eq(0).trigger(keyPressEvent(KEY.SPACE));

                    // Menu is closed, focus has been returned to container
                    // and file format is '.txt'.
                    /* TO DO
                    expect(speedControl.focus).toHaveBeenCalled();
                    expect($('.video_speeds li[data-speed="1.50"]'))
                        .toHaveClass('active');
                    expect($('.speeds p.active')).toHaveHtml('1.50x');
                    */
                });

                // TO DO? No such behavior implemented.
                xit('TAB + SHIFT keydown on speed entry closes menu and gives ' +
                    'focus to Play/Pause control', function () {
                    // First open menu. Focus is on last speed entry.
                    speedControl.trigger(keyPressEvent(KEY.UP));
                    speedEntries.last().trigger(tabBackPressEvent());

                    // Menu is closed and focus has been given to Play/Pause
                    // control.
                    expect(state.videoControl.playPauseEl.focus)
                        .toHaveBeenCalled();
                });

                // TO DO? No such behavior implemented.
                xit('TAB keydown on speed entry closes menu and gives focus ' +
                   'to Volume control', function () {
                    // First open menu. Focus is on last speed entry.
                    speedControl.trigger(keyPressEvent(KEY.UP));
                    speedEntries.last().trigger(tabForwardPressEvent());

                    // Menu is closed and focus has been given to Volume
                    // control.
                    expect(state.videoVolumeControl.buttonEl.focus)
                        .toHaveBeenCalled();
                });
            });
        });

        // TODO
        xdescribe('change file format', function () {
            describe('when new file format is not the same', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayer();
                    state.videoSpeedControl.setSpeed(1.0);
                    spyOn(state.videoPlayer, 'onSpeedChange').and.callThrough();

                    $('li[data-speed="0.75"] .speed-link').click();
                });

                it('trigger speedChange event', function () {
                    expect(state.videoPlayer.onSpeedChange).toHaveBeenCalled();
                    expect(state.videoSpeedControl.currentSpeed).toEqual(0.75);
                });
            });
        });

        // TODO
        xdescribe('onSpeedChange', function () {
            beforeEach(function () {
                state = jasmine.initializePlayer();
                $('li[data-speed="1.0"] .speed-link').addClass('active');
                state.videoSpeedControl.setSpeed(0.75);
            });

            it('set the new speed as active', function () {
                expect($('.video_speeds li[data-speed="1.0"]'))
                    .not.toHaveClass('active');
                expect($('.video_speeds li[data-speed="0.75"]'))
                    .toHaveClass('active');
                expect($('.speeds p.active')).toHaveHtml('0.75x');
            });
        });
    });
}).call(this);
