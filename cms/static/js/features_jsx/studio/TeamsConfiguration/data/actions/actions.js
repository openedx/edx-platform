import { createAction } from '@reduxjs/toolkit';

const updateCourseMaxTeamSize = createAction('updateCourseMaxTeamSize');

const teamsConfig = {
  save: {
    started: createAction('teamsConfig/save/started'),
    success: createAction('teamsConfig/save/success'),
    failure: createAction('teamsConfig/save/failure'),
  },
  load: {
    started: createAction('teamsConfig/load/started'),
    success: createAction('teamsConfig/load/success'),
    failure: createAction('teamsConfig/load/failure'),
  },
};

const teamSet = {
  add: createAction('teamSet/add'),
  delete: createAction('teamSet/delete'),
  updateField: createAction('teamSet/update'),
};

const setTeamsConfigURL = createAction('setTeamsConfigURL');

export default {
  updateCourseMaxTeamSize,
  teamsConfig,
  teamSet,
  setTeamsConfigURL,
};
