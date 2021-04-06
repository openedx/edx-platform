/* global gettext */
import { InputText, Button } from '@edx/paragon';
import PropTypes from 'prop-types';
import React from 'react';
import _ from 'underscore';
import TeamSet from './TeamSet';

class TeamsConfiguration extends React.Component {
  constructor(props) {
    super(props);
    this.handleSaveConfigButtonClicked = this.handleSaveConfigButtonClicked.bind(this);
    this.renderMessages = this.renderMessages.bind(this);
  }

  componentDidMount() {
    this.props.initializeValues(
      this.props.initialTeamSets,
      this.props.initialCourseMaxTeamSize,
    );
  }

  handleSaveConfigButtonClicked() {
    this.props.handleSaveConfigButtonClicked(
      this.props.teamsConfigURL,
      this.props.teamSets,
      this.props.courseMaxTeamSize,
    );
  }

  renderMessages() {
    return (
      <div>
        {
          this.props.submit_failure && (
            <div className="errors">
              <span>{gettext('Could not save Teams Configuration:')}</span>
              <span>{this.props.errors}</span>
            </div>
          )
        }
        {
          this.props.submit_success && (
            <div className="success" background="green">
              <span>{gettext('Teams Configuration successfully saved')}</span>
            </div>
          )
        }
      </div>
    );
  }

  render() {
    return (
      <article className="content-primary settings-teams">
        { this.renderMessages() }
        <section className="group-settings teams-team-sets">
          <header>
            <h2 className="title-2">{gettext('Team Sets')}</h2>
            <span className="tip">{gettext('Placeholder tip for Team Sets')}</span>
          </header>
          <ol className="list-input course-team-sets-list enum">
            {
              _.keys(this.props.teamSets).map((uniqueTeamSetId) => {
                const teamSet = this.props.teamSets[uniqueTeamSetId];
                return (
                  <li className="field-group course-team-sets-list-item">
                    <TeamSet
                      key={uniqueTeamSetId}
                      uniqueTeamSetId={uniqueTeamSetId}
                      teamSetId={teamSet.teamSetId}
                      displayName={teamSet.displayName}
                      description={teamSet.description}
                      type={teamSet.type}
                      maxSize={teamSet.maxSize}
                      handleTeamSetChange={this.props.handleTeamSetChange}
                      handleDeleteTeamSet={this.props.handleDeleteTeamSetButtonClicked}
                    />
                  </li>
                );
              })
            }
          </ol>
          <Button
            label="Add a Team Set"
            onClick={this.props.handleAddTeamSetButtonClicked}
          />
        </section>
        <hr className="divide" />
        <section className="group-settings teams-max-size">
          <header>
            <h2 className="title-2">{gettext('Course Max Team Size')}</h2>
            <span className="tip">{gettext('Placeholder tip for Max Size')}</span>
          </header>
          <ol className="list-input">
            <li className="field text" id="field-course-max-team-size">
              <InputText
                label="Course Max Team Size"
                name="courseMaxTeamSize"
                value={this.props.courseMaxTeamSize}
                onChange={this.props.onCourseMaxTeamSizeChange}
              />
            </li>
          </ol>
        </section>
        <hr className="divide" />
        <Button
          label="Save Teams Configuration"
          name="saveTeamsConfig"
          onClick={this.handleSaveConfigButtonClicked}
        />
      </article>
    );
  }
}

TeamsConfiguration.defaultProps = {
  courseMaxTeamSize: 0,
  teamSets: {},
  submit_success: false,
  submit_failure: false,
  errors: [],
};

TeamsConfiguration.propTypes = {
  submit_success: PropTypes.bool,
  submit_failure: PropTypes.bool,
  errors: PropTypes.arrayOf(PropTypes.string),
  courseMaxTeamSize: PropTypes.number,
  teamSets: PropTypes.object.isRequired,
  // Outer props
  teamsConfigURL: PropTypes.string.isRequired,
  initialTeamSets: PropTypes.object.isRequired,
  initialCourseMaxTeamSize: PropTypes.number.isRequired,
  // dispatch
  initializeValues: PropTypes.func.isRequired,
  onCourseMaxTeamSizeChange: PropTypes.func.isRequired,
  handleTeamSetChange: PropTypes.func.isRequired,
  handleSaveConfigButtonClicked: PropTypes.func.isRequired,
  handleDeleteTeamSetButtonClicked: PropTypes.func.isRequired,
  handleAddTeamSetButtonClicked: PropTypes.func.isRequired,
};

export default TeamsConfiguration;
