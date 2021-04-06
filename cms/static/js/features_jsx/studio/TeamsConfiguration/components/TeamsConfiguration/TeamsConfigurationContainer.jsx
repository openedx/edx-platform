import { connect } from 'react-redux';
import { updateTeamSetField, updateCourseMaxTeamSize, addTeamSet, deleteTeamSet, saveTeamsConfig, initializeValues } from '../../data/actions/actions';
// import { getActiveBlockTree } from '../../data/selectors/index';
import TeamsConfiguration from './TeamsConfiguration';

function initialValueIfStateNull(stateValue, initialValue) {
  if (stateValue === null) {
    return initialValue;
  }
  return stateValue;
}

const mapStateToProps = (state, ownProps) => ({
  teamsConfigURL: ownProps.teamsConfigURL,
  teamSets: initialValueIfStateNull(
    state.teamSets,
    ownProps.initialTeamSets,
  ),
  courseMaxTeamSize: initialValueIfStateNull(
    state.courseMaxTeamSize,
    ownProps.initialCourseMaxTeamSize,
  ),
  submitting: state.saveState.submitting,
  submit_success: state.saveState.submit_success,
  submit_failure: state.saveState.submit_failure,
  errors: state.saveState.errors,
});

const mapDispatchToProps = {
  handleTeamSetChange: updateTeamSetField,
  onCourseMaxTeamSizeChange: updateCourseMaxTeamSize,
  handleAddTeamSetButtonClicked: addTeamSet,
  handleDeleteTeamSetButtonClicked: deleteTeamSet,
  handleSaveConfigButtonClicked: saveTeamsConfig,
  initializeValues,
};


const TeamsConfigurationContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(TeamsConfiguration);

export default TeamsConfigurationContainer;
