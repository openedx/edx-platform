(function (define) {
'use strict';
define('video/00_component.js', [],
function () {
     /**
     * Creates a new object with the specified prototype object and properties.
     * @param {Object} o The object which should be the prototype of the
     * newly-created object.
     * @private
     * @throws {TypeError, Error}
     * @return {Object}
     */
    var inherit = Object.create || (function () {
        var F = function () {};

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
    })();

    /**
     * Component module.
     * @exports video/00_component.js
     * @constructor
     * @return {jquery Promise}
     */
    var Component = function () {
        if ($.isFunction(this.initialize)) {
            return this.initialize.apply(this, arguments);
        }
    };

    /**
     * Returns new constructor that inherits form the current constructor.
     * @static
     * @param {Object} protoProps The object containing which will be added to
     * the prototype.
     * @return {Object}
     */
    Component.extend = function (protoProps, staticProps) {
        var Parent = this,
            Child = function () {
                if ($.isFunction(this.initialize)) {
                    return this.initialize.apply(this, arguments);
                }
            };

        // Inherit methods and properties from the Parent prototype.
        Child.prototype = inherit(Parent.prototype);
        Child.constructor = Parent;
        // Provide access to parent's methods and properties
        Child.__super__ = Parent.prototype;

        // Extends inherited methods and properties by methods/properties
        // passed as argument.
        if (protoProps) {
            $.extend(Child.prototype, protoProps);
        }

        // Inherit static methods and properties
        $.extend(Child, Parent, staticProps);

        return Child;
    };

    return Component;
});
}(RequireJS.define));
