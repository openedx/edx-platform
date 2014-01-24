(function (requirejs, require, define) {

define(
'video/00_cookie_storage.js',
[],
function() {
    "use strict";
/**
 * Provides convenient way to work with cookies.
 *
 * Maximum 4096 bytes can be stored per namespace.
 *
 * @TODO: Uses localStorage if available.
 *
 * @param {string} namespace Namespace that is used to store data.
 * @return {object} CookieStorage API.
 */
    var CookieStorage = function (namespace) {
        var Storage;

        /**
        * Returns an empty storage with proper data structure.
        *
        * @private
        * @return {object} Empty storage.
        */
        var _getEmptyStorage = function () {
            return {
                    storage: {},
                    keys: []
                };
        };

        /**
        * Returns the current value associated with the given namespace.
        * If data doesn't exist or has data with incorrect interface, it creates
        * an empty storage with proper data structure.
        *
        * @private
        * @param {string} namespace Namespace that is used to store data.
        * @return {object} Stored data or an empty storage.
        */
        var _getData = function (namespace) {
            var data;

            try {
                data = JSON.parse($.cookie(namespace));
            } catch (err) { }

            if (!data || !data['storage'] || !data['keys']) {
                return _getEmptyStorage();
            }

            return data;
        };

        /**
        * Clears cookies that has flag `session` equals true.
        *
        * @private
        */
        var _clearSession = function () {
            Storage['keys'] = $.grep(Storage['keys'], function(key_name, index) {
                if (Storage['storage'][key_name]['session']) {
                    delete Storage['storage'][key_name];

                    return false;
                }

                return true;
            });

            $.cookie(namespace, JSON.stringify(Storage), {
                expires: 3650,
                path: '/'
            });
        };

        /**
        * Adds new value to the storage or rewrites existent.
        *
        * @param {string} name Identifier of the data.
        * @param {any} value Data to store.
        * @param {boolean} useSession Data with this flag will be removed on
        *     window unload.
        */
        var setItem = function (name, value, useSession) {
            if (name) {
                if ($.inArray(name, Storage['keys']) === -1) {
                    Storage['keys'].push(name);
                }

                Storage['storage'][name] = {
                    value: value,
                    session: useSession ? true : false
                };

                $.cookie(namespace, JSON.stringify(Storage), {
                    expires: 3650,
                    path: '/'
                });
            }
        };

        /**
        * Returns the current value associated with the given name.
        *
        * @param {string} name Identifier of the data.
        * @return {any} The current value associated with the given name.
        *     If the given key does not exist in the list
        *     associated with the object then this method must return null.
        */
        var getItem = function (name) {
            try {
                return Storage['storage'][name]['value'];
            } catch (err) { }

            return null;
        };

        /**
        * Removes the current value associated with the given name.
        *
        * @param {string} name Identifier of the data.
        */
        var removeItem = function (name) {
            delete Storage['storage'][name];

            Storage['keys'] = $.grep(Storage['keys'], function(key_name, index) {
                return name !== key_name;
            });

            $.cookie(namespace, JSON.stringify(Storage), {
                expires: 3650,
                path: '/'
            });
        };

        /**
        * Empties the storage.
        *
        */
        var clear = function () {
            Storage = _getEmptyStorage();
            $.cookie(namespace, null, {
                expires: -1,
                path: '/'
            });
        };

        /**
        * Returns the name of the `n`th key in the list.
        *
        * @param {number} n Index of the key.
        * @return {string} Name of the `n`th key in the list.
        *     If `n` is greater than or equal to the number of key/value pairs
        *     in the object, then this method must return `null`.
        */
        var key = function (n) {
            if (n >= Storage['keys'].length) {
                return null;
            }

            return Storage['keys'][n];
        };

        /**
        * Initializes the module: creates a storage with proper namespace, binds
        * `unload` event.
        *
        * @private
        */
        (function initialize() {
            if (!namespace) {
                namespace = 'cookieStorage';
            }
            Storage = _getData(namespace);

            $(window).unload(_clearSession);
        }());

        return {
            clear: clear,
            getItem: getItem,
            key: key,
            removeItem: removeItem,
            setItem: setItem
        };
    };

    return CookieStorage;
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
