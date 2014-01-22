(function (requirejs, require, define) {
require(
['video/00_cookie_storage.js'],
function (CookieStorage) {
    describe('CookieStorage', function () {
        var mostRecentCall;

        beforeEach(function () {
            mostRecentCall = $.cookie.mostRecentCall;
        });

        afterEach(function () {
            CookieStorage('test_storage').clear();
        });

        describe('intialize', function () {
            it('with namespace', function () {
                var storage = CookieStorage('test_storage');

                storage.setItem('item_1', 'value_1');
                expect(mostRecentCall.args[0]).toBe('test_storage');
            });

            it('without namespace', function () {
                var storage = CookieStorage();

                storage.setItem('item_1', 'value_1');
                expect(mostRecentCall.args[0]).toBe('cookieStorage');
            });
        });

        it('unload', function () {
            var expected = JSON.stringify({
                    storage: {
                        'item_2': {
                            value: 'value_2',
                            session: false
                        }
                    },
                    keys: ['item_2']
                }),
                storage = CookieStorage('test_storage');

            storage.setItem('item_1', 'value_1', true);
            storage.setItem('item_2', 'value_2');

            $(window).trigger('unload');
            expect(mostRecentCall.args[1]).toBe(expected);
        });

        describe('methods: ', function () {
            var data = {
                    storage: {
                        'item_1': {
                            value: 'value_1',
                            session: false
                        }
                    },
                    keys: ['item_1']
                },
                storage;

            beforeEach(function () {
                $.cookie.andReturn(JSON.stringify(data));
                storage = CookieStorage('test_storage');
            });

            describe('setItem', function () {
                it('pass correct data', function () {
                    var expected = JSON.stringify({
                            storage: {
                                'item_1': {
                                    value: 'value_1',
                                    session: false
                                },
                                'item_2': {
                                    value: 'value_2',
                                    session: false
                                },
                                'item_3': {
                                    value: 'value_3',
                                    session: true
                                },
                            },
                            keys: ['item_1', 'item_2', 'item_3']
                        });

                    storage.setItem('item_2', 'value_2');
                    storage.setItem('item_3', 'value_3', true);
                    expect(mostRecentCall.args[0]).toBe('test_storage');
                    expect(mostRecentCall.args[1]).toBe(expected);
                });

                it('pass broken arguments', function () {
                    $.cookie.reset();
                    storage.setItem(null, 'value_1');
                    expect($.cookie).not.toHaveBeenCalled();
                });
            });

            describe('getItem', function () {
                it('item exist', function () {
                    $.each(data['storage'], function(key, value) {
                        expect(storage.getItem(key)).toBe(value['value']);
                    });
                });

                it('item does not exist', function () {
                    expect(storage.getItem('nonexistent')).toBe(null);
                });
            });

            describe('removeItem', function () {
                it('item exist', function () {
                    var expected = JSON.stringify({
                            storage: {},
                            keys: []
                        });

                    storage.removeItem('item_1');
                    expect(mostRecentCall.args[1]).toBe(expected);
                });

                it('item does not exist', function () {
                    storage.removeItem('nonexistent');
                    expect(mostRecentCall.args[1]).toBe(JSON.stringify(data));
                });
            });

            it('clear', function () {
                storage.clear();
                expect(mostRecentCall.args[1]).toBe(null);
            });

            describe('key', function () {
                it('key exist', function () {
                    $.each(data['keys'], function(index, name) {
                        expect(storage.key(index)).toBe(name);
                    });
                });

                it('key is grater than keys list', function () {
                    expect(storage.key(100)).toBe(null);
                });
            });
        });
    });
});
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
