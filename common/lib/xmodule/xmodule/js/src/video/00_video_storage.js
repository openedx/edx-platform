(function(requirejs, require, define) {
    define(
'video/00_video_storage.js',
[],
function() {
    'use strict';
/**
 * Provides convenient way to store key value pairs.
 *
 * @param {string} namespace Namespace that is used to store data.
 * @return {object} VideoStorage API.
 */
    var VideoStorage = function(namespace, id) {
        /**
        * Adds new value to the storage or rewrites existent.
        *
        * @param {string} name Identifier of the data.
        * @param {any} value Data to store.
        * @param {boolean} instanceSpecific Data with this flag will be added
        *     to instance specific storage.
        */
        var setItem = function(name, value, instanceSpecific) {
            if (name) {
                if (instanceSpecific) {
                    window[namespace][id][name] = value;
                } else {
                    window[namespace][name] = value;
                }
            }
        };

        /**
        * Returns the current value associated with the given name.
        *
        * @param {string} name Identifier of the data.
        * @param {boolean} instanceSpecific Data with this flag will be added
        *     to instance specific storage.
        * @return {any} The current value associated with the given name.
        *     If the given key does not exist in the list
        *     associated with the object then this method must return null.
        */
        var getItem = function(name, instanceSpecific) {
            if (instanceSpecific) {
                return window[namespace][id][name];
            } else {
                return window[namespace][name];
            }
        };

        /**
        * Removes the current value associated with the given name.
        *
        * @param {string} name Identifier of the data.
        * @param {boolean} instanceSpecific Data with this flag will be added
        *     to instance specific storage.
        */
        var removeItem = function(name, instanceSpecific) {
            if (instanceSpecific) {
                delete window[namespace][id][name];
            } else {
                delete window[namespace][name];
            }
        };

        /**
        * Empties the storage.
        *
        */
        var clear = function() {
            window[namespace] = {};
            window[namespace][id] = {};
        };

        /**
        * Initializes the module: creates a storage with proper namespace.
        *
        * @private
        */
        (function initialize() {
            if (!namespace) {
                namespace = 'VideoStorage';
            }
            if (!id) {
                // Generate random alpha-numeric string.
                id = Math.random().toString(36).slice(2);
            }

            window[namespace] = window[namespace] || {};
            window[namespace][id] = window[namespace][id] || {};
        }());

        return {
            clear: clear,
            getItem: getItem,
            removeItem: removeItem,
            setItem: setItem
        };
    };

    return VideoStorage;
});
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
