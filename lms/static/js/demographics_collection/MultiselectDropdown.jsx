import React, { useState } from 'react';
import PropTypes from 'prop-types';

class MultiselectDropdown extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      open: false,
    };

    // this version of React does not support React.createRef()
    this.buttonRef = null;
    this.setButtonRef = (element) => {
      this.buttonRef = element;
    }

    this.focusButton = this.focusButton.bind(this);
    this.handleKeydown = this.handleKeydown.bind(this);
    this.handleButtonClick = this.handleButtonClick.bind(this);
    this.handleRemoveAllClick = this.handleRemoveAllClick.bind(this);
    this.handleOptionClick = this.handleOptionClick.bind(this);
  }

  componentDidMount(){
    document.addEventListener("keydown", this.handleKeydown, false);
  }

  componentWillUnmount(){
    document.removeEventListener("keydown", this.handleKeydown, false);
  }

  findOption(data) {
    return this.props.options.find((o) => o.value == data || o.label == data);
  }

  focusButton() {
    if (this.buttonRef) this.buttonRef.focus();
  }

  handleKeydown(e) {
    if (this.state.open && event.keyCode == 27) {
      this.setState({ open: false }, this.focusButton);
    }
  }

  handleButtonClick(e) {
    this.setState({ open: !this.state.open });
  }

  handleRemoveAllClick(e) {
    this.props.onChange([]);
    this.focusButton();
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

  renderSelected() {
    if (this.props.selected.length == 0) {
      return this.props.emptyLabel;
    }

    return this.props.selected.map((value) => {
      return this.findOption(value).label;
    }).join(", ")
  }

  renderUnselect() {
    return this.props.selected.length > 0 && (
      <button id="unselect-button" onClick={this.handleRemoveAllClick}>x</button>
    )
  }

  renderMenu() {
    if (!this.state.open) {
      return;
    }

    const options = this.props.options.map((option, index) => {
      const checked = this.props.selected.includes(option.value);
      return (
        <div key={index} id={`${option.value}-option-container`} className="option-container">
          <label className="option-label">
            <input id={`${option.value}-option-checkbox`} className="option-checkbox" type="checkbox" value={option.value} checked={checked} onChange={this.handleOptionClick}/>
            {option.label}
          </label>
        </div>
      )
    })

    return (
      <fieldset id="multiselect-dropdown-fieldset">
        <legend className="sr-only">{this.props.label}</legend>
        {options}
      </fieldset>
    )
  }

  render() {
    return (
      <div className="multiselect-dropdown">
        <div id="multiselect-dropdown-label">{this.props.label}</div>
        <button id="multiselect-dropdown-button" type="button" ref={this.setButtonRef} aria-haspopup="true" aria-expanded={this.state.open} aria-labelledby="multiselect-dropdown-label multiselect-dropdown-button" onClick={this.handleButtonClick}>
          {this.renderSelected()}
          {this.renderUnselect()}
        </button>
        {this.renderMenu()}
      </div>
    )
  }
}

export { MultiselectDropdown };

MultiselectDropdown.propTypes = {
  label: PropTypes.string,
  emptyLabel: PropTypes.string,
  options: PropTypes.array.isRequired,
  selected: PropTypes.array.isRequired,
  onChange: PropTypes.func.isRequired,
};
