(function() {
    'use strict';

    describe('XBlockToXModuleShim', function() {
        describe('definition', function() {
            it('XBlockToXModuleShim is defined, and is a function', function() {
                expect($.isFunction(XBlockToXModuleShim)).toBe(true);
            });
        });

        describe('implementation', function() {
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
                    spyOn(window, 'None');
                    removeNone = false;
                } else {
                    window.None = jasmine.createSpy('None');
                    removeNone = true;
                }

                if (window.Video) {
                    spyOn(window, 'Video');
                    removeVideo = false;
                } else {
                    window.Video = jasmine.createSpy('Video');
                    removeVideo = true;
                }
                window.Video.and.returnValue(videoModule);

                editCallback = jasmine.createSpy('editCallback');
                $(document).on('XModule.loaded.edit', editCallback);
                spyOnEvent($(document), 'XModule.loaded.edit');

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

                expect(XBlockToXModuleShim(null, $el)).toBeUndefined();
                expect(window.None).not.toHaveBeenCalled();
            });

            it('if element module is of type Video, Video module constructor is called', function() {
                $el.data('type', 'Video');

                expect(XBlockToXModuleShim(null, $el)).toEqual(videoModule);
                expect(window.Video).toHaveBeenCalled();

                expect('XModule.loaded.edit').not.toHaveBeenTriggeredOn(document);
                expect('XModule.loaded.display').not.toHaveBeenTriggeredOn(document);
            });

            it('if element has class "xmodule_edit"', function() {
                $el.data('type', 'Video')
                    .addClass('xmodule_edit');
                XBlockToXModuleShim(null, $el);
                expect('XModule.loaded.edit').toHaveBeenTriggeredOn($(document));
                expect(editCallback).toHaveBeenCalledWith(jasmine.any($.Event), $el, videoModule);
                expect('XModule.loaded.display').not.toHaveBeenTriggeredOn($(document));
            });

            it('if element has class "xmodule_display"', function() {
                $el.data('type', 'Video')
                    .addClass('xmodule_display');
                XBlockToXModuleShim(null, $el);
                expect('XModule.loaded.edit').not.toHaveBeenTriggeredOn($(document));
                expect('XModule.loaded.display').toHaveBeenTriggeredOn($(document));
                expect(displayCallback).toHaveBeenCalledWith(jasmine.any($.Event), $el, videoModule);
            });

            it('if element has classes "xmodule_edit", and "xmodule_display"', function() {
                $el.data('type', 'Video')
                    .addClass('xmodule_edit')
                    .addClass('xmodule_display');
                XBlockToXModuleShim(null, $el);
                expect('XModule.loaded.edit').toHaveBeenTriggeredOn($(document));
                expect('XModule.loaded.display').toHaveBeenTriggeredOn($(document));
            });

            it('element is of an unknown Module type, console.error() is called if it is defined', function() {
                var oldConsole = window.console;

                if (window.console && window.console.error) {
                    spyOn(window.console, 'error');
                } else {
                    window.console = jasmine.createSpy('console.error');
                }

                $el.data('type', 'UnknownModule');
                expect(XBlockToXModuleShim(null, $el)).toBeUndefined();

                expect(console.error).toHaveBeenCalledWith(
                    'Unable to load UnknownModule: window[moduleType] is not a constructor'
                );

                window.console = oldConsole;
            });

            it('element is of an unknown Module type, JavaScript throws if console.error() is not defined', function() {
                var oldConsole = window.console,
                    testFunction = function() {
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
                expect($.isPlainObject(XModule)).toBe(true);
            });

            it('XModule.Descriptor is defined, and is a function', function() {
                expect($.isFunction(XModule.Descriptor)).toBe(true);
            });

            it('XModule.Descriptor has a complete prototype', function() {
                expect($.isFunction(XModule.Descriptor.prototype.onUpdate)).toBe(true);
                expect($.isFunction(XModule.Descriptor.prototype.update)).toBe(true);
                expect($.isFunction(XModule.Descriptor.prototype.save)).toBe(true);
            });
        });

        describe('implementation', function() {
            var el, obj, callback, length;

            // This is a dummy callback.
            callback = function() {
                var x = 1;

                return x + 1;
            };

            beforeEach(function() {
                el = 'dummy object';
                obj = new XModule.Descriptor(el);

                spyOn(obj, 'save').and.callThrough();
            });

            afterEach(function() {
                el = null;
                obj = null;

                length = undefined;
            });

            it('Descriptor is a proper constructor function', function() {
                expect(obj.hasOwnProperty('element')).toBe(true);
                expect(obj.element).toBe(el);

                expect(obj.hasOwnProperty('update')).toBe(true);
            });

            it('Descriptor.onUpdate called for the first time', function() {
                expect(obj.hasOwnProperty('callbacks')).toBe(false);
                obj.onUpdate(callback);
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
                var callback1 = jasmine.createSpy('callback1'),
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
