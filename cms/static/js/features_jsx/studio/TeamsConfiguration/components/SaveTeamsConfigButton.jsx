/* global gettext */
import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Button } from '@edx/paragon';
import thunkActions from '../data/actions/thunkActions';

export const SaveTeamsConfigButton = ({ onClick }) => (
  <Button
    label={gettext('Save Teams Configuration')}
    name="saveTeamsConfig"
    onClick={onClick}
  />
);

SaveTeamsConfigButton.propTypes = {
  onClick: PropTypes.func.isRequired,
};

const mapDispatchToProps = {
  onClick: thunkActions.save,
};

export default connect({}, mapDispatchToProps)(SaveTeamsConfigButton);
