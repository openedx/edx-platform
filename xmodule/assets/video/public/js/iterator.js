export class Iterator {
    /**
     * @param {Array} list - Array to be iterated.
     */
    constructor(list) {
        this.list = Array.isArray(list) ? list : [];
        this.index = 0;
        this.size = this.list.length;
        this.lastIndex = this.size - 1;
    }

    /**
     * Checks if the provided index is valid.
     * @param {number} index
     * @return {boolean}
     * @protected
     */
    _isValid(index) {
        return typeof index === 'number' &&
            Number.isInteger(index) &&
            index >= 0 &&
            index < this.size;
    }

    /**
     * Returns the next element and updates the current position.
     * @param {number} [index]
     * @return {any}
     */
    next(index = this.index) {
        if (!this._isValid(index)) {
            index = this.index;
        }

        this.index = (index >= this.lastIndex) ? 0 : index + 1;
        return this.list[this.index];
    }

    /**
     * Returns the previous element and updates the current position.
     * @param {number} [index]
     * @return {any}
     */
    prev(index = this.index) {
        if (!this._isValid(index)) {
            index = this.index;
        }

        this.index = (index < 1) ? this.lastIndex : index - 1;
        return this.list[this.index];
    }

    /**
     * Returns the last element in the list.
     * @return {any}
     */
    last() {
        return this.list[this.lastIndex];
    }

    /**
     * Returns the first element in the list.
     * @return {any}
     */
    first() {
        return this.list[0];
    }

    /**
     * Checks if the iterator is at the end.
     * @return {boolean}
     */
    isEnd() {
        return this.index === this.lastIndex;
    }
}
