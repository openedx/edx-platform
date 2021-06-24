/* global gettext */
import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

export const TeamsConfigMessages = ({ submitSuccess, submitFailure, errors }) => (
  <div>
    {
      submitFailure && (
        <div className="errors">
          <span>{gettext('Could not save Teams Configuration:')}</span>
          <span>{errors}</span>
        </div>
      )
    }
    {
      submitSuccess && (
        <div className="success" background="green">
          <span>{gettext('Teams Configuration successfully saved')}</span>
        </div>
      )
    }
  </div>
);
TeamsConfigMessages.defaultProps = {
  submitSuccess: false,
  submitFailure: false,
  errors: [],
};

TeamsConfigMessages.propTypes = {
  submitSuccess: PropTypes.bool,
  submitFailure: PropTypes.bool,
  errors: PropTypes.arrayOf(PropTypes.string),
};

const mapStateToProps = state => ({
  submitSuccess: state.app.submitSuccess,
  submitFailure: state.app.submitFailure,
  errors: state.app.errors,
});

export default connect(mapStateToProps)(TeamsConfigMessages);
