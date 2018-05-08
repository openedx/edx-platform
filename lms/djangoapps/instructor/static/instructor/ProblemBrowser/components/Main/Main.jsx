/* global gettext */
import { Button } from '@edx/paragon';
import BlockBrowserContainer from 'BlockBrowser/components/BlockBrowser/BlockBrowserContainer';
import * as PropTypes from 'prop-types';
import * as React from 'react';
import { PopupModalContainer } from '../Popup/PopupModalContainer';

export default class Main extends React.Component {
  constructor(props) {
    super(props);
    this.handleToggleDropdown = this.handleToggleDropdown.bind(this);
    this.showPopup = this.showPopup.bind(this);
    this.hidePopup = this.hidePopup.bind(this);
    this.state = {
      popupOpen: false,
      showDropdown: false,
      taskForBlock: null,
    };
  }

  handleToggleDropdown() {
    this.props.fetchCourseBlocks(this.props.courseId, this.props.excludeBlockTypes);
    this.setState({ showDropdown: !this.state.showDropdown });
  }

  hideDropdown() {
    this.setState({ showDropdown: false });
  }

  showPopup() {
    if (this.state.taskForBlock !== this.props.selectedBlock) {
      this.props.createProblemResponsesReportTask(
        this.props.initialEndpoint,
        this.props.taskStatusEndpoint,
        this.props.selectedBlock,
      );
    }
    this.setState({ popupOpen: true, taskForBlock: this.props.selectedBlock });
  }

  hidePopup() {
    if (this.props.timeout != null) {
      clearTimeout(this.props.timeout);
    }
    this.setState({ popupOpen: false, taskForBlock: null });
    this.props.resetProblemResponsesReportTask();
  }

  render() {
    const { selectedBlock, onSelectBlock } = this.props;

    return (
      <div className="problem-browser">
        <Button
          onClick={this.handleToggleDropdown}
          label={gettext('Select a section or problem')}
        />
        <input type="text" name="problem-location" value={selectedBlock} disabled />
        {this.state.showDropdown &&
        <BlockBrowserContainer
          onSelectBlock={(blockId) => {
            this.hideDropdown();
            onSelectBlock(blockId);
          }}
        />}
        <Button
          onClick={this.showPopup}
          name="list-problem-responses-csv"
          label={gettext('Create a report of problem responses')}
        />
        <PopupModalContainer
          open={this.state.popupOpen}
          onHide={this.hidePopup}
        />
      </div>
    );
  }
}

Main.propTypes = {
  courseId: PropTypes.string.isRequired,
  createProblemResponsesReportTask: PropTypes.func.isRequired,
  excludeBlockTypes: PropTypes.arrayOf(PropTypes.string),
  fetchCourseBlocks: PropTypes.func.isRequired,
  initialEndpoint: PropTypes.string.isRequired,
  onSelectBlock: PropTypes.func.isRequired,
  selectedBlock: PropTypes.string,
  resetProblemResponsesReportTask: PropTypes.func.isRequired,
  taskStatusEndpoint: PropTypes.string.isRequired,
  timeout: PropTypes.number,
};

Main.defaultProps = {
  excludeBlockTypes: null,
  selectedBlock: null,
  timeout: null,
};
