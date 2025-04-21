'use strict';

/**
 * Creates a new object with the specified prototype object and properties.
 * @param {Object} o The object which should be the prototype of the newly-created object.
 * @private
 * @throws {TypeError, Error}
 * @return {Object}
 */
const inherit = Object.create || (function () {
    const F = function () { };

    return function (o) {
        if (arguments.length > 1) {
            throw Error('Second argument not supported');
        }
        if (_.isNull(o) || _.isUndefined(o)) {
            throw Error('Cannot set a null [[Prototype]]');
        }
        if (!_.isObject(o)) {
            throw TypeError('Argument must be an object');
        }

        F.prototype = o;
        return new F();
    };
}());

/**
 * Component constructor function.
 * Calls `initialize()` if defined.
 * @returns {any}
 */
function Component() {
    if ($.isFunction(this.initialize)) {
        return this.initialize.apply(this, arguments);
    }
}

/**
 * Adds an `extend` method to the Component constructor.
 * Creates a subclass that inherits from Component.
 * @param {Object} protoProps - Prototype methods and properties.
 * @param {Object} staticProps - Static methods and properties.
 * @returns {Function} Child constructor.
 */
Component.extend = function (protoProps, staticProps) {
    const Parent = this;

    const Child = function () {
        if ($.isFunction(this.initialize)) {
            return this.initialize.apply(this, arguments);
        }
    };

    Child.prototype = inherit(Parent.prototype);
    Child.constructor = Parent;
    Child.__super__ = Parent.prototype;

    if (protoProps) {
        $.extend(Child.prototype, protoProps);
    }

    $.extend(Child, Parent, staticProps);

    return Child;
};

export { Component };
