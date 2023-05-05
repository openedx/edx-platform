/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
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
                            {/* eslint-disable-next-line react/button-has-type */}
                            <button className="btn btn-link" onClick={this.abortRequest}>{gettext('Cancel upload')}</button>
                        </span>
                        <div className="progress">
                            {/* eslint-disable-next-line jsx-a11y/control-has-associated-label */}
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
