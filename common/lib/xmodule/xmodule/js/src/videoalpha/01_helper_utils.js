// IE browser supports Function.bind() only starting with version 9.
//
// The bind function is a recent addition to ECMA-262, 5th edition; as such it may not be present in all
// browsers. You can partially work around this by inserting the following code at the beginning of your
// scripts, allowing use of much of the functionality of bind() in implementations that do not natively support
// it.
//
// https://developer.mozilla.org/en-US/docs/JavaScript/Reference/Global_Objects/Function/bind
if (!Function.prototype.bind) {
    Function.prototype.bind = function (oThis) {
        var aArgs, fToBind, fNOP, fBound;

        if (typeof this !== 'function') {
            // closest thing possible to the ECMAScript 5 internal IsCallable function
            throw new TypeError('Function.prototype.bind - what is trying to be bound is not callable');
        }

        aArgs = Array.prototype.slice.call(arguments, 1);
        fToBind = this;
        fNOP = function () {};
        fBound = function () {
            return fToBind.apply(
                this instanceof fNOP && oThis ? this : oThis,
                aArgs.concat(Array.prototype.slice.call(arguments))
            );
        };

        fNOP.prototype = this.prototype;
        fBound.prototype = new fNOP();

        return fBound;
    };
}

// IE browser supports Array.indexOf() only starting with version 9.
//
// indexOf is a recent addition to the ECMA-262 standard; as such it may not be present in all browsers. You can work
// around this by utilizing the following code at the beginning of your scripts. This will allow you to use indexOf
// when there is still no native support. This algorithm matches the one specified in ECMA-262, 5th edition, assuming
// Object, TypeError, Number, Math.floor, Math.abs, and Math.max have their original values.
//
// https://developer.mozilla.org/en-US/docs/JavaScript/Reference/Global_Objects/Array/indexOf
if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = function (searchElement /*, fromIndex */ ) {
        'use strict';
        if (this == null) {
            throw new TypeError();
        }
        var t = Object(this);
        var len = t.length >>> 0;
        if (len === 0) {
            return -1;
        }
        var n = 0;
        if (arguments.length > 1) {
            n = Number(arguments[1]);
            if (n != n) { // shortcut for verifying if it's NaN
                n = 0;
            } else if (n != 0 && n != Infinity && n != -Infinity) {
                n = (n > 0 || -1) * Math.floor(Math.abs(n));
            }
        }
        if (n >= len) {
            return -1;
        }
        var k = n >= 0 ? n : Math.max(len - Math.abs(n), 0);
        for (; k < len; k++) {
            if (k in t && t[k] === searchElement) {
                return k;
            }
        }
        return -1;
    }
}

if (!window.onTouchBasedDevice) {
    window.onTouchBasedDevice = function() {
        return navigator.userAgent.match(/iPhone|iPod|iPad/i);
    };
}
