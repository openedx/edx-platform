import Cookies from 'js-cookie';
import 'whatwg-fetch';
import _ from 'underscore';

const HEADERS = {
  Accept: 'application/json',
  'Content-Type': 'application/json',
  'X-CSRFToken': Cookies.get('csrftoken'),
};

const convertTeamSetToRequestFormat = function (teamSet) {
  const result = {
    type: teamSet.type,
  };
  if (teamSet.teamSetId) {
    result.id = teamSet.teamSetId;
  }
  if (teamSet.displayName) {
    result.name = teamSet.displayName;
  }
  if (teamSet.description) {
    result.description = teamSet.description;
  }
  if (teamSet.maxSize) {
    result.max_team_size = teamSet.maxSize;
  }
  return result;
};

export function requestSaveTeamsConfig(teamsConfigStudioURL, teamSets, courseMaxTeamSize) {
  const updateData = {};
  if (courseMaxTeamSize) {
    updateData.max_team_size = courseMaxTeamSize;
  }
  const teamSetUniqueIds = Object.keys(teamSets);
  if (teamSets && teamSetUniqueIds.length > 0) {
    updateData.team_sets = teamSetUniqueIds.map(
      teamSetUniqueId => convertTeamSetToRequestFormat(teamSets[teamSetUniqueId]),
    );
  }
  return fetch(teamsConfigStudioURL, {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify(updateData),
  });
}
