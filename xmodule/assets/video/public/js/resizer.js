import _ from 'underscore';

class Resizer {
    constructor(params) {
        const defaults = {
            container: window,
            element: null,
            containerRatio: null,
            elementRatio: null
        };
        this.callbacksList = [];
        this.delta = {
            height: 0,
            width: 0
        };
        this.mode = null;
        this.config = { ...defaults, ...params };

        if (!this.config.element) {
            console.log('Required parameter `element` is not passed.');
        }

        this.callbacks = {
            add: this.addCallback.bind(this),
            once: this.addOnceCallback.bind(this),
            remove: this.removeCallback.bind(this),
            removeAll: this.removeCallbacks.bind(this)
        };
        this.deltaApi = {
            add: this.addDelta.bind(this),
            substract: this.substractDelta.bind(this),
            reset: this.resetDelta.bind(this)
        };
    }

    getData() {
        const $container = this.config.container instanceof Window ? this.config.container : this.config.container;
        const containerWidth = ($container === window ? $container.innerWidth : $container.offsetWidth) + this.delta.width;
        const containerHeight = ($container === window ? $container.innerHeight : $container.offsetHeight) + this.delta.height;
        let containerRatio = this.config.containerRatio;

        const $element = this.config.element;
        let elementRatio = this.config.elementRatio;

        if (!containerRatio) {
            containerRatio = containerWidth / containerHeight;
        }

        if (!elementRatio && $element) {
            elementRatio = $element.offsetWidth / $element.offsetHeight;
        }

        return {
            containerWidth,
            containerHeight,
            containerRatio,
            element: $element,
            elementRatio
        };
    }

    align() {
        const data = this.getData();

        switch (this.mode) {
            case 'height':
                this.alignByHeightOnly(data);
                break;
            case 'width':
                this.alignByWidthOnly(data);
                break;
            default:
                if (data.containerRatio >= data.elementRatio) {
                    this.alignByHeightOnly(data);
                } else {
                    this.alignByWidthOnly(data);
                }
                break;
        }

        this.fireCallbacks();
        return this;
    }

    alignByWidthOnly(data = this.getData()) {
        if (!data.element) return this;
        const height = data.containerWidth / data.elementRatio;
        data.element.style.height = `${height}px`;
        data.element.style.width = `${data.containerWidth}px`;
        data.element.style.top = `${0.5 * (data.containerHeight - height)}px`;
        data.element.style.left = '0px';
        return this;
    }

    alignByHeightOnly(data = this.getData()) {
        if (!data.element) return this;
        const width = data.containerHeight * data.elementRatio;
        data.element.style.height = `${data.containerHeight}px`;
        data.element.style.width = `${width}px`;
        data.element.style.top = '0px';
        data.element.style.left = `${0.5 * (data.containerWidth - width)}px`;
        return this;
    }

    setMode(param) {
        if (_.isString(param)) {
            this.mode = param;
            this.align();
        }
        return this;
    }

    setElement(element) {
        this.config.element = element;
        return this;
    }

    addCallback(func) {
        if (_.isFunction(func)) {
            this.callbacksList.push(func);
        } else {
            console.error('[Video info]: TypeError: Argument is not a function.');
        }
        return this;
    }

    addOnceCallback(func) {
        if (_.isFunction(func)) {
            const decorator = () => {
                func();
                this.removeCallback(func);
            };
            this.addCallback(decorator);
        } else {
            console.error('TypeError: Argument is not a function.');
        }
        return this;
    }

    fireCallbacks() {
        this.callbacksList.forEach(callback => callback());
    }

    removeCallbacks() {
        this.callbacksList.length = 0;
        return this;
    }

    removeCallback(func) {
        const index = this.callbacksList.indexOf(func);
        if (index !== -1) {
            return this.callbacksList.splice(index, 1);
        }
        return undefined;
    }

    resetDelta() {
        this.delta.height = 0;
        this.delta.width = 0;
        return this;
    }

    addDelta(value, side) {
        if (_.isNumber(value) && _.isNumber(this.delta[side])) {
            this.delta[side] += value;
        }
        return this;
    }

    substractDelta(value, side) {
        if (_.isNumber(value) && _.isNumber(this.delta[side])) {
            this.delta[side] -= value;
        }
        return this;
    }

    destroy() {
        const data = this.getData();
        if (data.element) {
            data.element.style.height = '';
            data.element.style.width = '';
            data.element.style.top = '';
            data.element.style.left = '';
        }
        this.removeCallbacks();
        this.resetDelta();
        this.mode = null;
    }
}

export { Resizer };