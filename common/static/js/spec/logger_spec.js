(function() {
    'use strict';

    describe('Logger', function() {
        it('expose window.log_event', function() {
            // eslint-disable-next-line no-undef
            expect(window.log_event).toBe(Logger.log);
        });

        describe('log', function() {
            // Note that log is used by external XBlocks, and the API cannot change without
            // proper deprecation and notification for external authors.
            it('can send a request to log event', function() {
                // eslint-disable-next-line no-undef
                spyOn(jQuery, 'ajaxWithPrefix');
                // eslint-disable-next-line no-undef
                Logger.log('example', 'data');
                // eslint-disable-next-line no-undef
                expect(jQuery.ajaxWithPrefix).toHaveBeenCalledWith({
                    url: '/event',
                    type: 'POST',
                    data: {
                        event_type: 'example',
                        event: '"data"',
                        courserun_key: 'edX/999/test',
                        page: window.location.href
                    },
                    async: true
                });
            });

            it('can send a request with custom options to log event', function() {
                // eslint-disable-next-line no-undef
                spyOn(jQuery, 'ajaxWithPrefix');
                // eslint-disable-next-line no-undef
                Logger.log('example', 'data', null, {type: 'GET', async: false});
                // eslint-disable-next-line no-undef
                expect(jQuery.ajaxWithPrefix).toHaveBeenCalledWith({
                    url: '/event',
                    type: 'GET',
                    data: {
                        event_type: 'example',
                        event: '"data"',
                        courserun_key: 'edX/999/test',
                        page: window.location.href
                    },
                    async: false
                });
            });
        });

        describe('ajax request settings with path_prefix', function() {
            /* eslint-disable-next-line camelcase, no-var */
            var $meta_tag;

            beforeEach(function() {
                // eslint-disable-next-line no-undef
                this.initialAjaxWithPrefix = jQuery.ajaxWithPrefix;
                // eslint-disable-next-line no-undef
                AjaxPrefix.addAjaxPrefix($, _.bind(function() {
                    return $("meta[name='path_prefix']").attr('content');
                }, this));
            });

            afterEach(function() {
                // eslint-disable-next-line no-undef
                jQuery.ajaxWithPrefix = this.initialAjaxWithPrefix;
                // eslint-disable-next-line camelcase
                $meta_tag.remove();
                // eslint-disable-next-line camelcase
                $meta_tag = null;
            });

            it('if path_prefix is not defined', function() {
                // eslint-disable-next-line camelcase
                $meta_tag = $('<meta name="path_prefix1" content="">');
                // eslint-disable-next-line camelcase
                $meta_tag.appendTo('body');
                // eslint-disable-next-line no-undef
                spyOn(jQuery, 'ajax');
                // eslint-disable-next-line no-undef
                Logger.log('example', 'data');
                // eslint-disable-next-line no-undef
                expect(jQuery.ajax).toHaveBeenCalledWith({
                    url: 'undefined/event',
                    type: 'POST',
                    data: {
                        event_type: 'example',
                        event: '"data"',
                        courserun_key: 'edX/999/test',
                        page: window.location.href
                    },
                    async: true
                });
            });

            it('if path_prefix is defined', function() {
                // eslint-disable-next-line camelcase
                $meta_tag = $('<meta name="path_prefix" content="">');
                // eslint-disable-next-line camelcase
                $meta_tag.appendTo('body');
                // eslint-disable-next-line no-undef
                spyOn(jQuery, 'ajax');
                // eslint-disable-next-line no-undef
                Logger.log('example', 'data');
                // eslint-disable-next-line no-undef
                expect(jQuery.ajax).toHaveBeenCalledWith({
                    url: '/event',
                    type: 'POST',
                    data: {
                        event_type: 'example',
                        event: '"data"',
                        courserun_key: 'edX/999/test',
                        page: window.location.href
                    },
                    async: true
                });
            });

            it('if path_prefix is custom value', function() {
                // eslint-disable-next-line camelcase
                $meta_tag = $('<meta name="path_prefix" content="testpath">');
                // eslint-disable-next-line camelcase
                $meta_tag.appendTo('body');
                // eslint-disable-next-line no-undef
                spyOn(jQuery, 'ajax');
                // eslint-disable-next-line no-undef
                Logger.log('example', 'data');
                // eslint-disable-next-line no-undef
                expect(jQuery.ajax).toHaveBeenCalledWith({
                    url: 'testpath/event',
                    type: 'POST',
                    data: {
                        event_type: 'example',
                        event: '"data"',
                        courserun_key: 'edX/999/test',
                        page: window.location.href
                    },
                    async: true
                });
            });
        });

        describe('listen', function() {
            // Note that listen is used by external XBlocks, and the API cannot change without
            // proper deprecation and notification for external authors.
            beforeEach(function() {
                // eslint-disable-next-line no-undef
                spyOn(jQuery, 'ajaxWithPrefix');
                // eslint-disable-next-line no-undef
                this.callbacks = _.map(_.range(4), function() {
                    // eslint-disable-next-line no-undef
                    return jasmine.createSpy();
                });
                // eslint-disable-next-line no-undef
                Logger.listen('example', null, this.callbacks[0]);
                // eslint-disable-next-line no-undef
                Logger.listen('example', null, this.callbacks[1]);
                // eslint-disable-next-line no-undef
                Logger.listen('example', 'element', this.callbacks[2]);
                // eslint-disable-next-line no-undef
                Logger.listen('new_event', null, this.callbacks[3]);
            });

            it('can listen to events when the element name is unknown', function() {
                // eslint-disable-next-line no-undef
                Logger.log('example', 'data');
                expect(this.callbacks[0]).toHaveBeenCalledWith('example', 'data', null);
                expect(this.callbacks[1]).toHaveBeenCalledWith('example', 'data', null);
                expect(this.callbacks[2]).not.toHaveBeenCalled();
                expect(this.callbacks[3]).not.toHaveBeenCalled();
            });

            it('can listen to events when the element name is known', function() {
                // eslint-disable-next-line no-undef
                Logger.log('example', 'data', 'element');
                expect(this.callbacks[0]).not.toHaveBeenCalled();
                expect(this.callbacks[1]).not.toHaveBeenCalled();
                expect(this.callbacks[2]).toHaveBeenCalledWith('example', 'data', 'element');
                expect(this.callbacks[3]).not.toHaveBeenCalled();
            });

            it('can catch exceptions', function() {
                // eslint-disable-next-line no-var
                var callback = function() {
                    // eslint-disable-next-line no-undef
                    Logger.log('exception', 'data');
                };
                // eslint-disable-next-line no-undef
                Logger.listen('exception', null, function() {
                    throw new Error();
                });
                expect(callback).not.toThrow();
                // eslint-disable-next-line no-undef
                expect(jQuery.ajaxWithPrefix).toHaveBeenCalled();
            });
        });

        describe('bind', function() {
            // Note that bind may be used by external XBlocks, and the API cannot change without
            // proper deprecation and notification for external authors.
            beforeEach(function() {
                // eslint-disable-next-line no-undef
                this.initialPostWithPrefix = jQuery.postWithPrefix;
                // eslint-disable-next-line no-undef
                this.initialGetWithPrefix = jQuery.getWithPrefix;
                // eslint-disable-next-line no-undef
                this.initialAjaxWithPrefix = jQuery.ajaxWithPrefix;
                this.prefix = '/6002x';
                // eslint-disable-next-line no-undef
                AjaxPrefix.addAjaxPrefix($, _.bind(function() {
                    return this.prefix;
                }, this));
                // eslint-disable-next-line no-undef
                Logger.bind();
            });

            afterEach(function() {
                // eslint-disable-next-line no-undef
                jQuery.postWithPrefix = this.initialPostWithPrefix;
                // eslint-disable-next-line no-undef
                jQuery.getWithPrefix = this.initialGetWithPrefix;
                // eslint-disable-next-line no-undef
                jQuery.ajaxWithPrefix = this.initialAjaxWithPrefix;
                window.onunload = null;
            });

            it('can bind the onunload event', function() {
                // eslint-disable-next-line no-undef
                expect(window.onunload).toEqual(jasmine.any(Function));
            });

            it('can send a request to log event', function() {
                // eslint-disable-next-line no-undef
                spyOn(jQuery, 'ajax');
                window.onunload();
                // eslint-disable-next-line no-undef
                expect(jQuery.ajax).toHaveBeenCalledWith({
                    url: this.prefix + '/event',
                    type: 'GET',
                    data: {
                        event_type: 'page_close',
                        event: '',
                        page: window.location.href
                    },
                    async: false
                });
            });
        });
    });
}).call(this);
