/* global gettext */

import React from 'react';
import PropTypes from 'prop-types';

class ShowProgress extends React.Component {
    constructor(props) {
        super(props);
        this.abortRequest = this.abortRequest.bind(this);
    }

    abortRequest(e) {
        e.preventDefault();
        this.props.request.abort();
    }

    render() {
        return (
            <div className="row">
                <div className="col-sm-12">
                    <div className="form-group">
                        <span className="file-name">{this.props.fileName}</span>
                        <span className="file-action abort-upload">
                            <button className="btn btn-link" onClick={this.abortRequest}>{gettext('Cancel upload')}</button>
                        </span>
                        <div className="progress">
                            <div className="progress-bar progress-bar-striped zero-width" role="progressbar" />
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

ShowProgress.propTypes = {
    fileName: PropTypes.string.isRequired,
    request: PropTypes.objectOf(XMLHttpRequest).isRequired,
};

export default ShowProgress;
