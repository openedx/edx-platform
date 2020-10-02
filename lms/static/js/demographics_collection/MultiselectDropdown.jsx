/* global gettext */
import React from 'react';
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

  componentDidMount() {
    document.addEventListener("keydown", this.handleKeydown, false);
  }

  componentWillUnmount() {

    document.removeEventListener("keydown", this.handleKeydown, false);
  }

  findOption(data) {
    return this.props.options.find((o) => o.value == data || o.display_name == data);
  }

  focusButton() {
    if (this.buttonRef) this.buttonRef.focus();
  }

  handleKeydown(event) {
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
    const selectedList = this.props.selected
      .map(selected => this.findOption(selected).display_name)
      .join(', ');
    if (selectedList.length > 60) {
      return selectedList.substring(0, 55) + '...'
    }
    return selectedList;
  }

  renderUnselect() {
    return this.props.selected.length > 0 && (
      <button id="unselect-button" disabled={this.props.disabled} aria-label="Clear all selected" onClick={this.handleRemoveAllClick}>{gettext("Clear all")}</button>
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
            <input id={`${option.value}-option-checkbox`} className="option-checkbox" type="checkbox" value={option.value} checked={checked} onChange={this.handleOptionClick} />
            <span className="pl-2">{option.display_name}</span>
          </label>
        </div>
      )
    })

    return (
      <fieldset id="multiselect-dropdown-fieldset" disabled={this.props.disabled}>
        <legend className="sr-only">{this.props.label}</legend>
        {options}
      </fieldset>
    )
  }

  render() {
    return (
      <div
        className="multiselect-dropdown pb-3"
        tabIndex={-1}
        onBlur={e => {
          // We need to make sure we only close and save the dropdown when
          // the user blurs on the parent to an element other than it's children.
          // essentially what this if statement is saying:
          // if the newly focused target is NOT a child of the this element, THEN fire the onBlur function
          // and close the dropdown.
          if (!e.currentTarget.contains(e.relatedTarget)) {
            this.props.onBlur(e);
            this.setState({ open: false })
          }
        }}
      >
        <label id="multiselect-dropdown-label" htmlFor="multiselect-dropdown">{this.props.label}</label>
        <div className="form-control d-flex">
          <button className="multiselect-dropdown-button" disabled={this.props.disabled} id="multiselect-dropdown-button" ref={this.setButtonRef} aria-haspopup="true" aria-expanded={this.state.open} aria-labelledby="multiselect-dropdown-label multiselect-dropdown-button" onClick={this.handleButtonClick}>
            {this.renderSelected()}
          </button>
          {this.renderUnselect()}
        </div>
        <div>
          {this.renderMenu()}
        </div>
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
