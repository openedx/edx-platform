import { dataUpdateActions, saveActions, teamSetActions } from './constants';
import { requestSaveTeamsConfig } from '../client';

const updateTeamSetField = (newValue, teamSetFieldName, uniqueTeamSetId) => ({
  type: dataUpdateActions.UPDATE_TEAMSET_FIELD,
  uniqueTeamSetId,
  teamSetFieldName,
  newValue,
});

const updateCourseMaxTeamSize = courseMaxTeamSize => ({
  type: dataUpdateActions.UPDATE_COURSE_MAX_TEAMS_SIZE,
  courseMaxTeamSize,
});

const saveTeamsConfigStarted = () => ({
  type: saveActions.SAVE_CONFIG_STARTED,
});

const saveTeamsConfigSuccess = () => ({
  type: saveActions.SAVE_CONFIG_SUCCESS,
});

const saveTeamsConfigFailure = error => ({
  type: saveActions.SAVE_CONFIG_FAILURE,
  error,
});

const saveTeamsConfig = (teamsConfigURL, teamSets, courseMaxTeamSize) => (dispatch) => {
  dispatch(saveTeamsConfigStarted());
  return requestSaveTeamsConfig(teamsConfigURL, teamSets, courseMaxTeamSize)
    .then(
      () => dispatch(saveTeamsConfigSuccess()),
      error => dispatch(saveTeamsConfigFailure(error)),
    );
};

const addTeamSet = () => ({
  type: teamSetActions.ADD_TEAM_SET,
});

const deleteTeamSet = uniqueTeamSetId => ({
  type: teamSetActions.DELETE_TEAM_SET,
  uniqueTeamSetId,
});

const initializeValues = (teamSets, courseMaxTeamSize) => ({
  type: dataUpdateActions.INITIALIZE_VALUES,
  teamSets,
  courseMaxTeamSize,
});


export {
  updateTeamSetField,
  updateCourseMaxTeamSize,
  saveTeamsConfig,
  saveTeamsConfigSuccess,
  saveTeamsConfigFailure,
  addTeamSet,
  deleteTeamSet,
  initializeValues,
};
