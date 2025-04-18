function isObject(val) {
    return typeof val === 'object' && val !== null;
}

function isFunction(val) {
    return typeof val === 'function';
}

/**
 * Polyfill-style safe object inheritance.
 * Equivalent to `Object.create()` but more robust for legacy use cases.
 * @param {Object} o
 * @returns {Object}
 */
function inherit(o) {
    if (arguments.length > 1) {
        throw new Error('Second argument not supported');
    }
    if (o === null || o === undefined) {
        throw new Error('Cannot set a null [[Prototype]]');
    }
    if (!isObject(o)) {
        throw new TypeError('Argument must be an object');
    }

    return Object.create(o);
}

/**
 * Base Component class with extend() support
 */
export class Component {
    constructor(...args) {
        if (isFunction(this.initialize)) {
            return this.initialize(...args);
        }
    }

    /**
     * Creates a subclass of the current Component.
     * @param {Object} protoProps - Prototype methods
     * @param {Object} staticProps - Static methods
     * @returns {Function} Subclass
     */
    static extend(protoProps = {}, staticProps = {}) {
        const Parent = this;

        class Child extends Parent {
            constructor(...args) {
                super(...args);
                if (isFunction(this.initialize)) {
                    return this.initialize(...args);
                }
            }
        }

        // Extend prototype with instance methods
        Object.assign(Child.prototype, protoProps);

        // Extend constructor with static methods
        Object.assign(Child, Parent, staticProps);

        // Reference to parent’s prototype (optional, for legacy support)
        Child.__super__ = Parent.prototype;

        return Child;
    }
}
