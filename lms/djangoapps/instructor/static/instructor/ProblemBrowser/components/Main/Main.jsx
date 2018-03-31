import * as React from 'react';
import * as PropTypes from 'prop-types';
import {Button} from '@edx/paragon';
import {BlockBrowserContainer} from '../BlockBrowser/BlockBrowserContainer';

export default class Main extends React.Component {
    constructor(props) {
        super(props);
        this.handleToggleDropdown = this.handleToggleDropdown.bind(this);
        this.state = {
            showDropdown: false,
        };
    }

    handleToggleDropdown() {
        this.props.fetchCourseBlocks(this.props.courseId);
        this.setState({showDropdown: !this.state.showDropdown});
    }

    hideDropdown() {
        this.setState({showDropdown: false});
    }

    render() {
        const {selectedBlock, onSelectBlock} = this.props;

        return (
            <div className="problem-browser">
                <Button onClick={this.handleToggleDropdown} label={gettext("Pick course block")}/>
                <input type="text" name="problem-location" value={selectedBlock} disabled/>
                {this.state.showDropdown &&
                <BlockBrowserContainer onSelectBlock={(blockId) => {
                    this.hideDropdown();
                    onSelectBlock(blockId);
                }}/>}
            </div>
        );
    }
}

Main.propTypes = {
    courseId: PropTypes.string.isRequired,
    fetchCourseBlocks: PropTypes.func.isRequired,
    onSelectBlock: PropTypes.func.isRequired,
    selectedBlock: PropTypes.string.isRequired,
};
