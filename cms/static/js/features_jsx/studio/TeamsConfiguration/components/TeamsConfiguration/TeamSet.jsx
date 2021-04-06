/* global gettext */
import { Button, Icon, InputText, InputSelect } from '@edx/paragon';
import PropTypes from 'prop-types';
import React from 'react';
import _ from 'underscore';

const typeValues = [
  { value: 'open', label: 'Open' },
  { value: 'public_managed', label: 'Public Managed' },
  { value: 'private_managed', label: 'Private Managed' },
];

const isValidTypeValue = (type) => {
  let isValid = false;
  typeValues.forEach((typeValue) => {
    if (!isValid) {
      isValid = type === typeValue.value;
    }
  });
  return isValid;
};

const typeValue = (type) => {
  if (isValidTypeValue(type)) {
    return type;
  }
  return 'open';
};

const TeamSet = ({ uniqueTeamSetId, teamSetId, displayName, description, type, maxSize, handleTeamSetChange, handleDeleteTeamSet }) => (
  <div className="teamset field">
    <InputText
      name="teamSetId"
      label="Team Set ID"
      value={teamSetId}
      onChange={(targetValue, targetName) => handleTeamSetChange(targetValue, targetName, uniqueTeamSetId)} // Paragon.asInput calls onChange with these params
    />
    <br />
    <InputText
      name="displayName"
      label="Display Name"
      value={displayName}
      onChange={(targetValue, targetName) => handleTeamSetChange(targetValue, targetName, uniqueTeamSetId)}
    />
    <br />
    <InputText
      name="description"
      label="Description"
      value={description}
      onChange={(targetValue, targetName) => handleTeamSetChange(targetValue, targetName, uniqueTeamSetId)}
    />
    <br />
    <InputSelect
      name="type"
      label="Teamset Type"
      value={typeValue(type)}
      options={typeValues}
      onChange={(targetValue, targetName) => handleTeamSetChange(targetValue, targetName, uniqueTeamSetId)}
    />
    <br />
    <InputText
      name="maxSize"
      label="Max Team Size"
      value={maxSize}
      onChange={(targetValue, targetName) => handleTeamSetChange(targetValue, targetName, uniqueTeamSetId)}
    />
    <br />
    <Button
      name="deleteTeamSet"
      label="Delete"
      onClick={() => handleDeleteTeamSet(uniqueTeamSetId)}
    />
  </div>
  );
TeamSet.propTypes = {
  uniqueTeamSetId: PropTypes.string.isRequired,
  teamSetId: PropTypes.string,
  displayName: PropTypes.string,
  description: PropTypes.string,
  type: PropTypes.string,
  maxSize: PropTypes.number,
  handleTeamSetChange: PropTypes.func.isRequired,
  handleDeleteTeamSet: PropTypes.func.isRequired,
};

TeamSet.defaultProps = {
  teamSetId: '',
  name: '',
  description: '',
  displayName: '',
  type: 'open',
  maxSize: 0,
};

export default TeamSet;
