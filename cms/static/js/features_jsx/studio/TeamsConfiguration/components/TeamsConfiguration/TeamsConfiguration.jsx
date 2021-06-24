/* global gettext */
import { connect } from 'react-redux';
import React from 'react';
import _ from 'underscore';
import TeamsConfigMessages from '../TeamsConfigMessages';
import CourseMaxTeamSize from '../CourseMaxTeamSize';
import TeamSetsSection from '../TeamSetsSection';
import { SaveTeamsConfigButton } from '../SaveTeamsConfigButton';
import thunkActions from '../../data/actions/thunkActions';

class TeamsConfiguration extends React.Component {
  constructor(props) {
    super(props);
  }

  componentDidMount() {
    this.props.initializeApp(
      this.props.teamsConfigURL
    )
  }

  renderForm() {
    return (
      <>
        <TeamsConfigMessages />
        <TeamSetsSection />
        <hr className="divide" />
        <CourseMaxTeamSize />
        <hr className="divide" />
        <SaveTeamsConfigButton />
      </>
    );
  }

  renderLoadFailure = () => (
    <>
    There was an error loading your teams configuration. Try reloading the page.
    </>
  )

  renderLoading = () => (
    <>
    Loading....
    </>
  )

  renderPageContents() {
    if (this.props.loadSuccess) {
      return renderForm();
    } else if (this.props.loadFailure) {
      return renderLoadFailure();
    } else {
      return renderLoading();
    }
  }

  render = () => (
    <article className="content-primary settings-teams">
      {this.renderPageContents()}
    </article>
  )
}

const mapStateToProps = (state, ownProps) => ({
  loading: state.app.loading,
  loaded: state.app.loadSuccess,
  loadFailed: state.app.loadFailure,
  teamsConfigURL: ownProps.teamsConfigURL,
});

const mapDispatchToProps = {
  initializeApp: thunkActions.initializeApp,
};

export default connect(mapStateToProps, mapDispatchToProps)(TeamsConfiguration);
