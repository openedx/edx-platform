import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import Dropdown from 'paragon/dist/Dropdown.js';

export class DropdownRenderer {
  constructor({selector, context}) {
    ReactDOM.render(
      <Dropdown {...context} />,
      document.querySelector(selector)
    );
  }
}
