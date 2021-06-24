import { combineReducers } from 'redux';
import { actions } from '../actions/actions';
import _ from 'underscore';


function parseMaxTeamSize(maxSize) {
  const numberMaxSize = parseInt(maxSize, 10);
  if (isNaN(numberMaxSize)) {
    return 0;
  }
  return numberMaxSize;
}

function getNewTeamsetFieldValue({ teamSetFieldName, newValue }) {
  let result = newValue;
  if (teamSetFieldName === 'maxSize') {
    result = parseMaxTeamSize(newValue);
  }
  return result;
}

const newBlankEmptyTeamSet = { type: 'open' };

export const teamSets = (state = {}, { type, payload }) => {
  switch (type) {
    case actions.teamsConfig.load.success.toString():
      // TODO: this
      return {
        ...state,
      };
    case actions.updateTeamSetField.toString():
      return {
        ...state,
        [payload.uniqueTeamSetId]: {
          ...state[payload.uniqueTeamSetId],
          [payload.teamSetFieldName]: getNewTeamsetFieldValue(payload),
        },
      };
    case actions.teamSets.add.toString(): {
      const uniqueTeamSetId = _.uniqueId('team_set');
      return {
        ...state,
        [uniqueTeamSetId]: _.clone(newBlankEmptyTeamSet),
      };
    }
    case actions.teamSets.delete.toString(): {
      const newState = {
        ...state,
      };
      delete newState[payload];
      return newState;
    }
    default:
      return state;
  }
};

export const courseMaxTeamSize = (state = 0, { type, payload }) => {
  switch (type) {
    case actions.updateCourseMaxTeamSize.toString():
      return parseMaxTeamSize(payload.courseMaxTeamSize);
    default:
      return state;
  }
};

const initialAppState = {
  teamsConfigURL: null,
  submitting: false,
  submitSuccess: false,
  submitFailure: false,
  loading: false,
  loadSuccess: false,
  loadFailure: false,
  errors: [],
};

export const app = (state = initialAppState, { type, payload }) => {
  switch (type) {
    case actions.setTeamsConfigUrl.toString():
      return {
        ...state,
        teamsConfigURL: payload,
      };
    case actions.teamsConfig.save.started.toString():
      return {
        ...state,
        submitting: true,
        errors: [],
      };
    case actions.teamsConfig.save.success.toString():
      return {
        ...state,
        submitting: false,
        submitSuccess: true,
        errors: [],
      };
    case actions.teamsConfig.save.failure.toString():
      return {
        ...state,
        submitting: false,
        submitFailure: true,
        errors: [payload.error],
      };
    case actions.teamsConfig.load.started.toString():
      return {
        ...state,
        loading: true,
      };
    case actions.teamsConfig.load.success.toString():
      return {
        ...state,
        loading: false,
        loadSuccess: true,
      };
    case actions.teamsConfig.load.failure.toString():
      return {
        ...state,
        loading: false,
        loadFailure: true,
      };
    default:
      return state;
  }
};

export default combineReducers({
  teamSets,
  courseMaxTeamSize,
  app,
});
