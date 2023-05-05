/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
/* global gettext */
/* eslint react/no-array-index-key: 0 */

import React from 'react';
import PropTypes from 'prop-types';

// eslint-disable-next-line react/prefer-stateless-function
class ShowErrors extends React.Component {
    render() {
        return (
            this.props.hasErrors && (
                <div className="col-sm-12">
                    <div className="alert alert-danger" role="alert">
                        <strong>{gettext('Please fix the following errors:')}</strong>
                        <ul>
                            {
                                Object.keys(this.props.errorList).map(key => this.props.errorList[key]
                                && <li key={key}>{this.props.errorList[key]}</li>)
                            }
                        </ul>
                    </div>
                </div>
            ));
    }
}

ShowErrors.propTypes = {
    errorList: PropTypes.objectOf(PropTypes.string).isRequired,
    hasErrors: PropTypes.bool.isRequired,
};

export default ShowErrors;
