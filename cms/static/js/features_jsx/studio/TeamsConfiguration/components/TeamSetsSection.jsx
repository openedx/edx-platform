/* global gettext */
import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import TeamSet from './TeamsConfiguration/TeamSet';
import AddTeamSetButton from './AddTeamSetButton';
import _ from 'underscore';

export const TeamSetsSection = ({ uniqueTeamSetIds }) => (
  <section className="group-settings teams-team-sets">
    <header>
      <h2 className="title-2">{gettext('Team Sets')}</h2>
      <span className="tip">{gettext('Placeholder tip for Team Sets')}</span>
    </header>
    <ol className="list-input course-team-sets-list enum">
      {
        uniqueTeamSetIds.map(uniqueTeamSetId => (
          <li className="field-group course-team-sets-list-item">
            <TeamSet key={uniqueTeamSetId} uniqueTeamSetId={uniqueTeamSetId} />
          </li>
        ))
      }
    </ol>
    <AddTeamSetButton />
  </section>
);

TeamSetsSection.defaultProps = {
  uniqueTeamSetIds: [],
};

TeamSetsSection.propTypes = {
  uniqueTeamSetIds: PropTypes.arrayOf(PropTypes.string),
};

const mapStateToProps = state => ({
  uniqueTeamSetIds: _.keys(state.teamSets),
});

export default connect(mapStateToProps)(TeamSetsSection);
