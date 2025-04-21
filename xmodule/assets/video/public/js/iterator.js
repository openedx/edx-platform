'use strict';

/**
 * Provides a convenient way to work with iterable data.
 * @constructor
 * @param {Array} list Array to be iterated.
 */
function Iterator(list) {
    this.list = list;
    this.index = 0;
    this.size = this.list.length;
    this.lastIndex = this.list.length - 1;
}

Iterator.prototype = {
    /**
     * Checks validity of the provided index for the iterator.
     * @param {number} index
     * @return {boolean}
     */
    _isValid(index) {
        return _.isNumber(index) && index < this.size && index >= 0;
    },

    /**
     * Returns the next element.
     * @param {number} [index] Updates current position.
     * @return {any}
     */
    next(index) {
        if (!this._isValid(index)) {
            index = this.index;
        }

        this.index = (index >= this.lastIndex) ? 0 : index + 1;
        return this.list[this.index];
    },

    /**
     * Returns the previous element.
     * @param {number} [index] Updates current position.
     * @return {any}
     */
    prev(index) {
        if (!this._isValid(index)) {
            index = this.index;
        }

        this.index = (index < 1) ? this.lastIndex : index - 1;
        return this.list[this.index];
    },

    /**
     * Returns the last element in the list.
     * @return {any}
     */
    last() {
        return this.list[this.lastIndex];
    },

    /**
     * Returns the first element in the list.
     * @return {any}
     */
    first() {
        return this.list[0];
    },

    /**
     * Returns `true` if the current position is the last for the iterator.
     * @return {boolean}
     */
    isEnd() {
        return this.index === this.lastIndex;
    }
};

export { Iterator };