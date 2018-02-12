/*
Wrapper for React/Paragon accessible status bar
*/

import React from 'react';
import ReactDOM from 'react-dom';
import { StatusAlert } from '@edx/paragon/static';

export class StatusAlertRenderer {
  constructor(message, selector, afterselector) {
    this.shiftFocus = this.shiftFocus.bind(this);
    const element = document.querySelector(selector);

    if (element) {
      /*
      These props match the defaults mostly in the paragon lib:
      https://github.com/edx/paragon/tree/master/src/StatusAlert
      but are made explicit in the case of a upstream change to defaults
      */
      ReactDOM.render(
        <StatusAlert
          alertType='warning'
          dismissible={true}
          open={true}
          dialog={message}
          dismissable={true}
          onClose={() => this.shiftFocus(afterselector)}
        />,
        document.querySelector(selector)
      );
    }
  }

  shiftFocus(afterselector) {
    const afterelement = document.querySelector(afterselector);
    /*
    Optional generic function to shift 'next' focusable element for keyboard users
    */
    if (afterelement) {
      afterelement.focus();
    }
  }
}
