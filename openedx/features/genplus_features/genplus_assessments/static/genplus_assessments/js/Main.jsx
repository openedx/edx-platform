/* global gettext */
import { Button, Icon } from '@edx/paragon';
import BlockBrowserContainer from 'BlockBrowser/components/BlockBrowser/BlockBrowserContainer';
import * as PropTypes from 'prop-types';
import * as React from 'react';

import AddDeleteTableRows from "./AddDeleteTableRows";

export default class Main extends React.Component {
  constructor(props) {
    super(props);
    this.handleToggleDropdown = this.handleToggleDropdown.bind(this);
    this.handleSelectProgram = this.handleSelectProgram.bind(this);
    this.handleFormSubmit = this.handleFormSubmit.bind(this);
    this.state = {
      showDropdown: false,
      selectedProgram: ''
    };
  }

  handleToggleDropdown() {
    this.props.fetchCourseBlocks(this.props.baseUrl, this.props.courseId, this.props.excludeBlockTypes);
    this.setState({ showDropdown: !this.state.showDropdown });
  }

  hideDropdown() {
    this.setState({ showDropdown: false });
  }

  handleSelectProgram(event){
    this.setState({
      selectedProgram: event.target.value
    });
  };

  handleFormSubmit(event){
    event.preventDefault();
    console.log("You have submitted:", this.state.selectedProgram);
  };


  render() {
    const { selectedBlock, onSelectBlock, programsWithUnits } = this.props;
    let selectorType = <Button onClick={this.handleToggleDropdown} label={gettext('Select a section or problem')} />;
    if (this.props.showBtnUi === 'false') {
      selectorType =
          // eslint-disable-next-line jsx-a11y/no-static-element-interactions
        (<span
          onClick={this.handleToggleDropdown}
          className={['problem-selector']}
        >
          <span>{selectedBlock || 'Select a section or problem'}</span>
          <span className={['pull-right']}>
            <Icon
              className={['fa', 'fa-sort']}
            />
          </span>
        </span>);
    }


    return (
      <div className="problem-browser-container">
        <form onSubmit={this.handleFormSubmit}>
          <div className="form-group">
            <select
              value={this.state.selectedProgram}
              onChange={this.handleSelectProgram}
              className="form-control"
              id="select-program"
            >
              <option value="">Select Program</option>
              {
                Object.entries(programsWithUnits).map(([key, value], index) => (
                  <option key={index} value={key}>{key}</option>
                ))
              }
            </select>
            {/* <select
              value={this.state.selectedProgram}
              onChange={this.handleSelectProgram}
              className="form-control"
              id="select-program"
            >
              <option value="">Select Intro Unit</option>
              {
                Object.entries(programsWithUnits).map(([key, value], index)=>(<option key={index} value={key}>{key}</option>))
              }
            </select> */}
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={this.state.selectedValue === "noProgram"}
          >
            Submit
          </button>
        </form>
        <div className="problem-browser">
          {selectorType}
          <span>{selectedBlock}</span>
          {this.state.showDropdown &&
            <BlockBrowserContainer
              onSelectBlock={(blockId) => {
                this.hideDropdown();
                onSelectBlock(blockId);
              }}
            />}
        </div>
        {
          this.state.selectedProgram !== "" &&
          <AddDeleteTableRows unitKeys={programsWithUnits[this.state.selectedProgram]}/>
        }
      </div>
    );
  }
}

Main.propTypes = {
  baseUrl: PropTypes.string.isRequired,
  courseId: PropTypes.string.isRequired,
  excludeBlockTypes: PropTypes.arrayOf(PropTypes.string),
  fetchCourseBlocks: PropTypes.func.isRequired,
  onSelectBlock: PropTypes.func.isRequired,
  selectedBlock: PropTypes.string,
};

Main.defaultProps = {
  excludeBlockTypes: null,
  selectedBlock: '',
  timeout: null,
};
