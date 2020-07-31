import React, { useState } from 'react';
import PropTypes from 'prop-types';

import { CheckBox } from '@edx/paragon/static';

class MultiselectDropdown extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      open: false,
    };

    this.handleButtonClick = this.handleButtonClick.bind(this);
    this.handleRemoveAllClick = this.handleRemoveAllClick.bind(this);
    this.handleOptionClick = this.handleOptionClick.bind(this);
  }

  findOption(data) {
    return this.props.options.find((o) => o.value == data || o.label == data);
  }

  displayValue() {
    if (this.props.selected.length == 0) {
      return this.props.emptyLabel;
    }

    return this.props.selected.map((value) => {
      return this.findOption(value).label;
    }).join(", ")
  }

  handleButtonClick(e) {
    this.setState({ open: !this.state.open });
  }

  handleRemoveAllClick(e) {
    this.props.onChange([]);
    e.stopPropagation();
  }

  handleOptionClick(e) {
    const value = e.target.value;
    const inSelected = this.props.selected.includes(value);
    let newSelected = [...this.props.selected];

    // if the option has its own onChange, trigger that instead
    if (this.findOption(value).onChange) {
      this.findOption(value).onChange(e.target.checked, value);
      return;
    }

    // if checked, add value to selected list
    if (e.target.checked && !inSelected) {
      newSelected = newSelected.concat(value);
    }

    // if unchecked, remove value from selected list
    if (!e.target.checked && inSelected) {
      newSelected = newSelected.filter(i => i !== value);
    }

    this.props.onChange(newSelected);
  }

  renderMenu() {
    const options = this.props.options.map((option, index) => {
      const checked = this.props.selected.includes(option.value);
      return (
        <div key={index}>
          <input type="checkbox" id={option.value} value={option.value} checked={checked} onChange={this.handleOptionClick}/>
          <label htmlFor={option.value}>{option.label}</label>
        </div>
      )
    })

    return (
      <div>
        {options}
      </div>
    )
  }

  render() {
    return (
      <div className="multiselect-dropdown">
        <button onClick={this.handleButtonClick}>
          {this.displayValue()}
          <button onClick={this.handleRemoveAllClick}>X</button>
        </button>
        {this.state.open && this.renderMenu()}
      </div>
    )
  }
}

export { MultiselectDropdown };

MultiselectDropdown.propTypes = {
  options: PropTypes.array.isRequired,
  selected: PropTypes.array.isRequired,
  onChange: PropTypes.func.isRequired,
};
