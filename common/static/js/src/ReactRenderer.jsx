import React from 'react';
import ReactDOM from 'react-dom';

class ReactRendererException extends Error {
    constructor(message) {
        super(`ReactRendererException: ${message}`);
        Error.captureStackTrace(this, ReactRendererException);
    }
}

export class ReactRenderer {
    constructor({ component, selector, componentName, props = {} }) {
        Object.assign(this, {
            component,
            selector,
            componentName,
            props,
        });
        this.handleArgumentErrors();
        this.targetElement = this.getTargetElement();
        this.renderComponent();
    }

    handleArgumentErrors() {
        if (this.component === null) {
            throw new ReactRendererException(
                `Component ${this.componentName} is not defined. Make sure you're ` +
        `using a non-default export statement for the ${this.componentName} ` +
        `class, that ${this.componentName} has an entry point defined ` +
        'within the \'entry\' section of webpack.common.config.js, and that the ' +
        'entry point is pointing at the correct file path.',
            );
        }
        if (!(this.props instanceof Object && this.props.constructor === Object)) {
            let propsType = typeof this.props;
            if (Array.isArray(this.props)) {
                propsType = 'array';
            } else if (this.props === null) {
                propsType = 'null';
            }
            throw new ReactRendererException(
                `Invalid props passed to component ${this.componentName}. Expected ` +
        `an object, but received a ${propsType}.`,
            );
        }
    }

    getTargetElement() {
        const elementList = document.querySelectorAll(this.selector);
        if (elementList.length !== 1) {
            throw new ReactRendererException(
                `Expected 1 element match for selector "${this.selector}" ` +
        `but received ${elementList.length} matches.`,
            );
        } else {
            return elementList[0];
        }
    }

    renderComponent() {
        ReactDOM.render(
            React.createElement(this.component, this.props, null),
            this.targetElement,
        );
    }
}
