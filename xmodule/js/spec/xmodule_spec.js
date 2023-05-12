(function() {
    'use strict';

    describe('XBlockToXModuleShim', function() {
        describe('definition', function() {
            it('XBlockToXModuleShim is defined, and is a function', function() {
                // eslint-disable-next-line no-undef
                expect($.isFunction(XBlockToXModuleShim)).toBe(true);
            });
        });

        describe('implementation', function() {
            // eslint-disable-next-line no-var
            var $el,
                videoModule = {
                    module: 'video_module'
                },
                editCallback,
                displayCallback,
                removeNone,
                removeVideo;

            beforeEach(function() {
                $el = $('<div />');

                if (window.None) {
                    // eslint-disable-next-line no-undef
                    spyOn(window, 'None');
                    removeNone = false;
                } else {
                    // eslint-disable-next-line no-undef
                    window.None = jasmine.createSpy('None');
                    removeNone = true;
                }

                if (window.Video) {
                    // eslint-disable-next-line no-undef
                    spyOn(window, 'Video');
                    removeVideo = false;
                } else {
                    // eslint-disable-next-line no-undef
                    window.Video = jasmine.createSpy('Video');
                    removeVideo = true;
                }
                window.Video.and.returnValue(videoModule);

                // eslint-disable-next-line no-undef
                editCallback = jasmine.createSpy('editCallback');
                $(document).on('XModule.loaded.edit', editCallback);
                spyOnEvent($(document), 'XModule.loaded.edit');

                // eslint-disable-next-line no-undef
                displayCallback = jasmine.createSpy('displayCallback');
                $(document).on('XModule.loaded.display', displayCallback);
                spyOnEvent($(document), 'XModule.loaded.display');
            });

            afterEach(function() {
                $el = null;

                if (removeNone) {
                    window.None = undefined;
                }
                if (removeVideo) {
                    window.Video = undefined;
                }
            });

            it('if element module is of type None, nothing happens', function() {
                $el.data('type', 'None');

                // eslint-disable-next-line no-undef
                expect(XBlockToXModuleShim(null, $el)).toBeUndefined();
                expect(window.None).not.toHaveBeenCalled();
            });

            it('if element module is of type Video, Video module constructor is called', function() {
                $el.data('type', 'Video');

                // eslint-disable-next-line no-undef
                expect(XBlockToXModuleShim(null, $el)).toEqual(videoModule);
                expect(window.Video).toHaveBeenCalled();

                expect('XModule.loaded.edit').not.toHaveBeenTriggeredOn(document);
                expect('XModule.loaded.display').not.toHaveBeenTriggeredOn(document);
            });

            it('if element has class "xmodule_edit"', function() {
                $el.data('type', 'Video')
                    .addClass('xmodule_edit');
                // eslint-disable-next-line no-undef
                XBlockToXModuleShim(null, $el);
                expect('XModule.loaded.edit').toHaveBeenTriggeredOn($(document));
                // eslint-disable-next-line no-undef
                expect(editCallback).toHaveBeenCalledWith(jasmine.any($.Event), $el, videoModule);
                expect('XModule.loaded.display').not.toHaveBeenTriggeredOn($(document));
            });

            it('if element has class "xmodule_display"', function() {
                $el.data('type', 'Video')
                    .addClass('xmodule_display');
                // eslint-disable-next-line no-undef
                XBlockToXModuleShim(null, $el);
                expect('XModule.loaded.edit').not.toHaveBeenTriggeredOn($(document));
                expect('XModule.loaded.display').toHaveBeenTriggeredOn($(document));
                // eslint-disable-next-line no-undef
                expect(displayCallback).toHaveBeenCalledWith(jasmine.any($.Event), $el, videoModule);
            });

            it('if element has classes "xmodule_edit", and "xmodule_display"', function() {
                $el.data('type', 'Video')
                    .addClass('xmodule_edit')
                    .addClass('xmodule_display');
                // eslint-disable-next-line no-undef
                XBlockToXModuleShim(null, $el);
                expect('XModule.loaded.edit').toHaveBeenTriggeredOn($(document));
                expect('XModule.loaded.display').toHaveBeenTriggeredOn($(document));
            });

            it('element is of an unknown Module type, console.error() is called if it is defined', function() {
                // eslint-disable-next-line no-var
                var oldConsole = window.console;

                if (window.console && window.console.error) {
                    // eslint-disable-next-line no-undef
                    spyOn(window.console, 'error');
                } else {
                    // eslint-disable-next-line no-undef
                    window.console = jasmine.createSpy('console.error');
                }

                $el.data('type', 'UnknownModule');
                // eslint-disable-next-line no-undef
                expect(XBlockToXModuleShim(null, $el)).toBeUndefined();

                // eslint-disable-next-line no-console
                expect(console.error).toHaveBeenCalledWith(
                    'Unable to load UnknownModule: window[moduleType] is not a constructor'
                );

                window.console = oldConsole;
            });

            it('element is of an unknown Module type, JavaScript throws if console.error() is not defined', function() {
                // eslint-disable-next-line no-var
                var oldConsole = window.console,
                    testFunction = function() {
                        // eslint-disable-next-line no-undef
                        return XBlockToXModuleShim(null, $el);
                    };

                if (window.console) {
                    window.console = undefined;
                }

                $el.data('type', 'UnknownModule');
                expect(testFunction).toThrow();

                window.console = oldConsole;
            });
        });
    });

    describe('XModule.Descriptor', function() {
        describe('definition', function() {
            it('XModule is defined, and is a plain object', function() {
                // eslint-disable-next-line no-undef
                expect($.isPlainObject(XModule)).toBe(true);
            });

            it('XModule.Descriptor is defined, and is a function', function() {
                // eslint-disable-next-line no-undef
                expect($.isFunction(XModule.Descriptor)).toBe(true);
            });

            it('XModule.Descriptor has a complete prototype', function() {
                // eslint-disable-next-line no-undef
                expect($.isFunction(XModule.Descriptor.prototype.onUpdate)).toBe(true);
                // eslint-disable-next-line no-undef
                expect($.isFunction(XModule.Descriptor.prototype.update)).toBe(true);
                // eslint-disable-next-line no-undef
                expect($.isFunction(XModule.Descriptor.prototype.save)).toBe(true);
            });
        });

        describe('implementation', function() {
            // eslint-disable-next-line no-var
            var el, obj, callback, length;

            // This is a dummy callback.
            callback = function() {
                // eslint-disable-next-line no-var
                var x = 1;

                return x + 1;
            };

            beforeEach(function() {
                el = 'dummy object';
                // eslint-disable-next-line no-undef
                obj = new XModule.Descriptor(el);

                // eslint-disable-next-line no-undef
                spyOn(obj, 'save').and.callThrough();
            });

            afterEach(function() {
                el = null;
                obj = null;

                length = undefined;
            });

            it('Descriptor is a proper constructor function', function() {
                // eslint-disable-next-line no-prototype-builtins
                expect(obj.hasOwnProperty('element')).toBe(true);
                expect(obj.element).toBe(el);

                // eslint-disable-next-line no-prototype-builtins
                expect(obj.hasOwnProperty('update')).toBe(true);
            });

            it('Descriptor.onUpdate called for the first time', function() {
                // eslint-disable-next-line no-prototype-builtins
                expect(obj.hasOwnProperty('callbacks')).toBe(false);
                obj.onUpdate(callback);
                // eslint-disable-next-line no-prototype-builtins
                expect(obj.hasOwnProperty('callbacks')).toBe(true);
                expect($.isArray(obj.callbacks)).toBe(true);

                length = obj.callbacks.length;
                expect(length).toBe(1);
                expect(obj.callbacks[length - 1]).toBe(callback);
            });

            it('Descriptor.onUpdate called for Nth time', function() {
                // In this test it doesn't matter what obj.callbacks
                // consists of.
                obj.callbacks = ['test1', 'test2', 'test3'];

                obj.onUpdate(callback);

                length = obj.callbacks.length;
                expect(length).toBe(4);
                expect(obj.callbacks[length - 1]).toBe(callback);
            });

            it('Descriptor.save returns a blank object', function() {
                // NOTE: In the future the implementation of .save()
                // method may change!
                expect(obj.save()).toEqual({});
            });

            it('Descriptor.update triggers all callbacks with whatever .save() returns', function() {
                /* eslint-disable-next-line no-undef, no-var */
                var callback1 = jasmine.createSpy('callback1'),
                    // eslint-disable-next-line no-undef
                    callback2 = jasmine.createSpy('callback2'),
                    testValue = 'test 123';

                obj.onUpdate(callback1);
                obj.onUpdate(callback2);

                obj.save.and.returnValue(testValue);
                obj.update();

                expect(callback1).toHaveBeenCalledWith(testValue);
                expect(callback2).toHaveBeenCalledWith(testValue);
            });
        });
    });
}).call(this);
