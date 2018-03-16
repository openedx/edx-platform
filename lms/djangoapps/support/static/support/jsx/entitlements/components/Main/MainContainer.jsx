import { connect } from 'react-redux';

import { dismissError } from '../../data/actions/error';
import Main from './Main.jsx';


const mapStateToProps = state => ({
  errorMessage: state.error,
});

const mapDispatchToProps = dispatch => ({
  dismissErrorMessage: () => dispatch(dismissError()),
});

const MainContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(Main);

export default MainContainer;
