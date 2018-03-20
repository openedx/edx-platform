import { connect } from 'react-redux';

import { dismissError } from '../../data/actions/error';
import { openCreationModal } from '../../data/actions/modal';

import Main from './Main.jsx';


const mapStateToProps = state => ({
  errorMessage: state.error,
});

const mapDispatchToProps = dispatch => ({
  dismissErrorMessage: () => dispatch(dismissError()),
  openCreationModal: () => dispatch(openCreationModal())
});

const MainContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Main);

export default MainContainer;
