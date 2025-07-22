/*
Wrapper for React/Paragon accessible status bar
*/

import React from 'react';
import ReactDOM from 'react-dom';
import {Alert} from '@openedx/paragon';

// eslint-disable-next-line import/prefer-default-export
export class StatusAlertRenderer {
    constructor(message, selector, afterselector) {
        this.shiftFocus = this.shiftFocus.bind(this);
        const element = document.querySelector(selector);

        if (element) {
            /*
      These props match the defaults mostly in the paragon lib:
      https://github.com/openedx/paragon/tree/master/src/StatusAlert
      but are made explicit in the case of a upstream change to defaults
      */
            ReactDOM.render(
                <Alert
                    variant="warning"
                    dismissible
                    show
                    onClose={() => this.shiftFocus(afterselector)}
                >
                    {message}
                </Alert>,
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
