import 'babel-polyfill';
import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';

class ReactRendererException extends Error {
  constructor(message) {
    super(`ReactRendererException: ${message}`);
    Error.captureStackTrace(this, ReactRendererException);
  }
}

export class ReactRenderer { // eslint-disable-line import/prefer-default-export
  constructor({ component, id, componentName, props = {}, store }) {
    Object.assign(this, {
      component,
      id,
      componentName,
      props,
      store,
    });
    this.handleArgumentErrors();
    document.addEventListener('DOMContentLoaded', this.renderComponent.bind(this));
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
    const elementList = document.querySelectorAll(`#${this.id}`);
    const targetList = document.querySelectorAll(
      `#renderReact-${this.id}`,
    );
    let targetElement;

    if (elementList.length > 1) {
      // target element is not unique
      throw new ReactRendererException(
        'Expected 1 target element match for id selector ' +
        `"${this.id}" but received ${elementList.length} matches. ` +
        'Please specify a unique destination id.',
      );
    }

    if (targetList.length > 1) {
      // selector is already in use for a different component
      throw new ReactRendererException(
        `The id "${this.id}" is already in use for a different ` +
        'React component on this page. Please specify a different ' +
        'target id.',
      );
    }

    if (elementList.length === 1) {
      // component is being rendered into an existing element
      targetElement = elementList[0];
      targetList[0].parentNode.removeChild(targetList[0]);
    } else {
      // component is being rendered in-place
      targetElement = document.createElement('div');
      targetElement.id = this.id;
      targetList[0].appendChild(targetElement);
    }

    return targetElement;
  }

  renderComponent() {
    const targetElement = this.getTargetElement();
    let el = React.createElement(this.component, this.props, null);
    if (this.store) {
      el = React.createElement(Provider, {
        store: this.store,
      }, el);
    }

    ReactDOM.render(
      el,
      targetElement,
    );
  }
}
