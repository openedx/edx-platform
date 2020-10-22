/* global gettext */
import { Button } from '@edx/paragon';
import { BlockBrowser } from 'BlockBrowser';
import * as PropTypes from 'prop-types';
import * as React from 'react';

export default class Main extends React.Component {
  constructor(props) {
    super(props);
    this.handleToggleDropdown = this.handleToggleDropdown.bind(this);
    this.state = {
      showDropdown: false,
    };
  }

  handleToggleDropdown() {
    this.props.fetchCourseBlocks(this.props.courseId, this.props.excludeBlockTypes);
    this.setState({ showDropdown: !this.state.showDropdown });
  }

  hideDropdown() {
    this.setState({ showDropdown: false });
  }

  render() {
    const { selectedBlock, onSelectBlock } = this.props;

    return (
      <div className="problem-browser">
        <Button onClick={this.handleToggleDropdown} label={gettext('Select a section or problem')} />
        <input type="text" name="problem-location" value={selectedBlock} disabled />
        {this.state.showDropdown &&
        <BlockBrowser onSelectBlock={(blockId) => {
          this.hideDropdown();
          onSelectBlock(blockId);
        }}
        />}
      </div>
    );
  }
}

Main.propTypes = {
  courseId: PropTypes.string.isRequired,
  excludeBlockTypes: PropTypes.arrayOf(PropTypes.string),
  fetchCourseBlocks: PropTypes.func.isRequired,
  onSelectBlock: PropTypes.func.isRequired,
  selectedBlock: PropTypes.string,
};

Main.defaultProps = {
  excludeBlockTypes: null,
  selectedBlock: null,
};
