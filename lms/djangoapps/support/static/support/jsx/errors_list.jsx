/* global gettext */
/* eslint react/no-array-index-key: 0 */

import React from 'react';
import PropTypes from 'prop-types';

class ShowErrors extends React.Component {
  render() {
    return (
      this.props.hasErrors && <div className="col-sm-12">
        <div className="alert alert-danger" role="alert">
          <strong>{gettext('Please fix the following errors:')}</strong>
          <ul>
            { Object.keys(this.props.errorList).map(key =>
              this.props.errorList[key] && <li key={key}>{this.props.errorList[key]}</li>,
            )}
          </ul>
        </div>
      </div>);
  }
}

ShowErrors.propTypes = {
  errorList: PropTypes.objectOf(PropTypes.string).isRequired,
  hasErrors: PropTypes.bool.isRequired,
};

export default ShowErrors;
