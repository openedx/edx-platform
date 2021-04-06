import { combineReducers } from 'redux';
import { dataUpdateActions, saveActions, teamSetActions } from '../actions/constants';
import _ from 'underscore';

/**
*
dataUpdateActions = {
  UPDATE_TEAMSET_FIELD: 'UPDATE_TEAMSET',
  UPDATE_COURSE_MAX_TEAMS_SIZE: 'UPDATE_COURSE_MAX_TEAM_SIZE'
};

export const saveActions = {
  SAVE_CONFIG_CLICKED: 'SAVE_CONFIG_CLICKED',
  SAVE_CONFIG_SUCCESS: 'SAVE_CONFIG_SUCCESS',
  SAVE_CONFIG_FAILURE: 'SAVE_CONFIG_FAILURE',
};

export const teamSetActions = {
  ADD_TEAM_SET: 'ADD_TEAM_SET',
  DELETE_TEAM_SET: 'DELETE_TEAM_SET'
};
*/

function parseMaxTeamSize(maxSize) {
  const numberMaxSize = parseInt(maxSize, 10);
  if (isNaN(numberMaxSize)) {
    return 0;
  }
  return numberMaxSize;
}

const newBlankEmptyTeamSet = { type: 'open' };

export const teamSets = (state = {}, action) => {
  const newState = { ...state };
  switch (action.type) {
    case dataUpdateActions.INITIALIZE_VALUES:
      return action.teamSets;
    case dataUpdateActions.UPDATE_TEAMSET_FIELD:
      const targetTeamSet = newState[action.uniqueTeamSetId];
      if (action.teamSetFieldName === 'maxSize') {
        targetTeamSet[action.teamSetFieldName] = parseMaxTeamSize(action.newValue);
      } else {
        targetTeamSet[action.teamSetFieldName] = action.newValue;
      }
      return newState;
    case teamSetActions.ADD_TEAM_SET:
      const uniqueTeamSetId = _.uniqueId('team_set');
      newState[uniqueTeamSetId] = _.clone(newBlankEmptyTeamSet);
      return newState;
    case teamSetActions.DELETE_TEAM_SET:
      delete newState[action.uniqueTeamSetId];
      return newState;
    default:
      return state;
  }
};

export const courseMaxTeamSize = (state = 0, action) => {
  switch (action.type) {
    case dataUpdateActions.UPDATE_COURSE_MAX_TEAMS_SIZE:
    case dataUpdateActions.INITIALIZE_VALUES:
      return parseMaxTeamSize(action.courseMaxTeamSize);
    default:
      return state;
  }
};

export const saveState = (state = {}, action) => {
  switch (action.type) {
    case saveActions.SAVE_CONFIG_CLICKED:
      return {
        ...state,
        submitting: true,
        errors: [],
      };
    case saveActions.SAVE_CONFIG_SUCCESS:
      return {
        ...state,
        submitting: false,
        submit_success: true,
        errors: [],
      };
    case saveActions.SAVE_CONFIG_FAILURE:
      return {
        ...state,
        submitting: false,
        submit_failure: true,
        errors: [action.error],
      };
    default:
      return {
        ...state,
        submitting: false,
        submit_success: false,
        submit_failure: false,
        errors: [],
      };
  }
};

export default combineReducers({
  teamSets,
  courseMaxTeamSize,
  saveState,
});
