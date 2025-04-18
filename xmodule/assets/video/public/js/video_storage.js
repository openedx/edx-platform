'use strict';

console.log('In video_storage.js file');

/**
 * Provides a convenient way to store key-value pairs.
 *
 * @param {string} namespace Namespace that is used to store data.
 * @param {string} id Identifier for instance-specific storage.
 * @return {object} VideoStorage API.
 */
export function VideoStorage(namespace = 'VideoStorage', id = Math.random().toString(36).slice(2)) {
    /**
     * Adds new value to the storage or rewrites existent.
     *
     * @param {string} name Identifier of the data.
     * @param {any} value Data to store.
     * @param {boolean} instanceSpecific Data with this flag will be added
     *     to instance specific storage.
     */
    const setItem = (name, value, instanceSpecific) => {
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
    const getItem = (name, instanceSpecific) => {
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
    const removeItem = (name, instanceSpecific) => {
        if (instanceSpecific) {
            delete window[namespace][id][name];
        } else {
            delete window[namespace][name];
        }
    };

    /** Clear the storage. */
    const clear = () => {
        window[namespace] = {};
        window[namespace][id] = {};
    };

    window[namespace] = window[namespace] || {};
    window[namespace][id] = window[namespace][id] || {};

    return {
        clear: clear,
        getItem: getItem,
        removeItem: removeItem,
        setItem: setItem
    };
}
