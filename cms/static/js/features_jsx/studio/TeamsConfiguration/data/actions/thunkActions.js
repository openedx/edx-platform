import { requestLoadTeamsConfig, requestSaveTeamsConfig } from '../client';
import actions from '.actions';

export const initializeApp = teamsConfigURL => (
  (dispatch) => {
    dispatch(actions.setTeamsConfigURL(teamsConfigURL));
    dispatch(loadTeamsConfig);
  }
);

export const saveTeamsConfig = () => (
  (dispatch, getState) => {
    dispatch(actions.teamSets.save.started());
    return requestSaveTeamsConfig(
      getState(), teamsConfigURL, teamSets, courseMaxTeamSize,
    ).then(
        () => dispatch(actions.teamSets.load.success()),
        error => dispatch(actions.teamSets.load.failure(error)),
      );
  });

export const loadTeamsConfig = () => (
  (dispatch, getState) => {
    dispatch(actions.teamSets.load.started());
    return requestLoadTeamsConfig(getState()).then(
      data => dispatch(actions.teamSets.load.success(data)),
      error => dispatch(actions.teamSets.load.failure(error)),
    );
  });

export default { save: saveTeamsConfig, load: loadTeamsConfig };
