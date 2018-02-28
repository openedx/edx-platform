import { connect } from 'react-redux';

import * as actionCreators from '../../data/actions/actionCreators';
import Search from './Search';

const mapStateToProps = (state) => {
  return {
    entitlements: state.entitlements
  };
}

const mapDispatchToProps = (dispatch) => {
  return {
    fetchEntitlements: (email, username, course_key) => {
      dispatch(actionCreators.fetchEntitlements(email,username,course_key));
    }
  };
}

const SearchContainer = connect(
  mapStateToProps,
  mapDispatchToProps
)(Search);

export default SearchContainer;
