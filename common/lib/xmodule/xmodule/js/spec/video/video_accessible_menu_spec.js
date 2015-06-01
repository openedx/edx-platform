(function (undefined) {
    describe('Video Accessible Menu', function () {
        var state;

        afterEach(function () {
            $('source').remove();
            state.storage.clear();
        });

        describe('constructor', function () {
            describe('always', function () {
                var videoTracks, container, button, menu, menuItems,
                    menuItemsLinks;

                beforeEach(function () {
                    state = jasmine.initializePlayer();
                    videoTracks = $('.video-tracks');
                    container = videoTracks.children('.wrapper-more-actions');
                    button = container.children('.has-dropdown');
                    menuList = container.children('.dropdown-menu');
                    menuItems = menuList.children('.dropdown-item');
                    menuItemsLinks = menuItems.children('.action');
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
                    activeMenuItem = menuItems.filter('.is-active');
                    expect(activeMenuItem.length).toBe(1);

                    expect(activeMenuItem.children('.action'))
                        .toHaveData('value', 'srt');

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

                it('add ARIA attributes to button, menu, and menu items links',
                   function () {
                    expect(button).toHaveAttrs({
                        'aria-disabled': 'false',
                        'aria-haspopup': 'true',
                        'aria-expanded': 'false'
                    });

                    menuItemsLinks.each(function(){
                        expect($(this)).toHaveAttrs({
                            'aria-disabled': 'false'
                        });
                    });
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
                    videoTracks = $('.video-tracks');
                    container = videoTracks.children('.wrapper-more-actions');
                    button = container.children('.button-more.has-dropdown');
                    menuList = container.children('.dropdown-menu');
                    menuItems = menuList.children('.dropdown-item');
                    menuItemsLinks = menuItems.children('.action');
                    spyOn($.fn, 'focus').andCallThrough();
                });

                it('opens the menu on click', function () {
                    button.click();
                    expect(button).toHaveClass('is-active');
                    expect(menuList).toHaveClass('is-visible');
                });

                if('close the menu on outside click', function() {
                    $(window).click();
                    expect(menuList).not.toHaveClass('is-visible');
                    expect(button).not.toHaveClass('is-active');
                });

                it('open the menu on ENTER keydown', function () {
                    container.trigger(keyPressEvent(KEY.ENTER));
                    expect(container).toHaveClass('is-visible');
                    expect(button).toHaveClass('is-active');
                    expect(menuItemsLinks.last().focus).toHaveBeenCalled();
                });

                it('open the menu on SPACE keydown', function () {
                    container.trigger(keyPressEvent(KEY.SPACE));
                    expect(container).toHaveClass('is-visible');
                    expect(button).toHaveClass('is-active');
                    expect(menuItemsLinks.last().focus).toHaveBeenCalled();
                });

                it('open the menu on UP keydown', function () {
                    container.trigger(keyPressEvent(KEY.UP));
                    expect(container).toHaveClass('is-visible');
                    expect(button).toHaveClass('is-active');
                    expect(menuItemsLinks.last().focus).toHaveBeenCalled();
                });

                it('close the menu on ESCAPE keydown', function () {
                    container.trigger(keyPressEvent(KEY.ESCAPE));
                    expect(container).not.toHaveClass('is-visible');
                    expect(button).not.toHaveClass('is-active');
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
                    expect($.fn.focus.calls.length)
                        .toEqual(2*menuItemsLinks.length+1);
                });

                it('ESC keydown on menu item closes menu', function () {
                    // First open menu. Focus is on last speed entry.
                    container.trigger(keyPressEvent(KEY.UP));
                    menuItemsLinks.last().trigger(keyPressEvent(KEY.ESCAPE));

                    // Menu is closed and focus has been returned to speed
                    // control.
                    expect(container).not.toHaveClass('is-visible');
                    expect(container.focus).toHaveBeenCalled();
                });

                it('ENTER keydown on menu item selects its data and closes menu',
                   function () {
                    // First open menu.
                    container.trigger(keyPressEvent(KEY.UP));
                    // Focus on '.txt'
                    menuItemsLinks.eq(0).focus();
                    menuItemsLinks.eq(0).trigger(keyPressEvent(KEY.ENTER));
-                });
            });
        });

        // TODO
        xdescribe('change file format', function () {
            describe('when new file format is not the same', function () {
                beforeEach(function () {
                    state = jasmine.initializePlayer();
                    state.videoSpeedControl.setSpeed(1.0);
                    spyOn(state.videoPlayer, 'onSpeedChange').andCallThrough();

                    $('li[data-speed="0.75"] a').click();
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
                $('li[data-speed="1.0"] a').addClass('active');
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
