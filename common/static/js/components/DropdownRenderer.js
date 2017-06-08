import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import { Dropdown } from 'paragon';

export class DropdownRenderer {
  constructor({selector, context}) {
    console.log(context);




    ReactDOM.render(
      <Dropdown {...context} />,
      document.querySelector(selector)
    );
  }
}
