(function (define) {
define(
'video/00_iterator.js',
[],
function() {
"use strict";
    /**
     * @desc Provides convenient way to work with iterate able data.
     *
     * @param {array} list Array to be iterated.
     *
     */
    var Iterator = function (list) {
            this.list = list;
            this.index = 0;
            this.size = this.list.length;
            this.lastIndex = this.list.length - 1;
        };

    Iterator.prototype = {

        /**
         * @desc Returns `true` if current index is valid for the iterator.
         *
         * @access protected
         * @returns {boolean}
         *
         */
        _isValid: function (index) {
            return _.isNumber(index) && index < this.size && index >= 0;
        },

        /**
         * @desc Returns next element.
         *
         * @param {number} index If set, updates current index of iterator.
         * @returns {any}
         *
         */
        next: function (index) {
            if (!(this._isValid(index))) {
                index = this.index;
            }

            this.index = (index >= this.lastIndex) ? 0: index + 1;

            return this.list[this.index];
        },

        /**
         * @desc Returns previous element.
         *
         * @param {number} index If set, updates current index of iterator.
         * @returns {any}
         *
         */
        prev: function (index) {
            if (!(this._isValid(index))) {
                index = this.index;
            }

            this.index = (index < 1) ? this.lastIndex: index - 1;

            return this.list[this.index];
        },

        /**
         * @desc Returns last element in the list.
         *
         * @returns {any}
         *
         */
        last: function () {
            return this.list[this.lastIndex];
        },

        /**
         * @desc Returns first element in the list.
         *
         * @returns {any}
         *
         */
        first: function () {
            return this.list[0];
        },

        /**
         * @desc Returns `true` if current position is last for the iterator.
         *
         * @returns {boolean}
         *
         */
        isEnd: function () {
            return this.index === this.lastIndex;
        }
    };

    return Iterator;
});
}(RequireJS.define));

