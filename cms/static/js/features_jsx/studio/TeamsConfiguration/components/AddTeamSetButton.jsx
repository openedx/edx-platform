/* global gettext */
import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import actions from '../data/actions/actions';
import { Button } from '@edx/paragon';

export const AddTeamSetButton = ({ handleAddTeamSet }) => (
  <Button
    label={gettext('Add a Team Set')}
    onClick={handleAddTeamSet}
  />
);

AddTeamSetButton.propTypes = {
  handleAddTeamSet: PropTypes.func.isRequired,
};

const mapDispatchToProps = {
  handleAddTeamSet: actions.teamSet.add,
};

export default connect({}, mapDispatchToProps)(AddTeamSetButton);
