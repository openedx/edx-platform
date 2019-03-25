import { connect } from 'react-redux';

import { dismissError } from '../../data/actions/error';
import { openCreationForm } from '../../data/actions/form';

import Main from './Main.jsx';


const mapStateToProps = state => ({
  errorMessage: state.error,
  isFormOpen: state.form.isOpen,
});

const mapDispatchToProps = dispatch => ({
  dismissErrorMessage: () => dispatch(dismissError()),
  openCreationForm: () => dispatch(openCreationForm()),
});

const MainContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Main);

export default MainContainer;
