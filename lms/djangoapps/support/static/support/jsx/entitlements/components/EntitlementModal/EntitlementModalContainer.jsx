import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import * as actionCreators from '../../data/actions/actionCreators';
import EntitlementModal from './EntitlementModal';

const mapStateToProps = (state) => {
  //Maps pieces of the state to props for convenience
  const entitlement = state.modal.activeEntitlement
  const isReissue = entitlement !== null && entitlement !== undefined;
  return {
    isReissue: isReissue,
    isOpen: state.modal.isOpen,
    entitlementUuid: isReissue ? entitlement.uuid : '',
    courseUuid: isReissue ? entitlement.course_uuid : '',
    user: isReissue ? entitlement.user : '',
    mode: isReissue ? entitlement.mode : '',
  };
}

const mapDispatchToProps = (dispatch) => {
  // bindActionCreators should be replaced by explicit dispatching.
  return bindActionCreators(actionCreators, dispatch);
}

const EntitlementModalContainer = connect(
  mapStateToProps,
  mapDispatchToProps
)(EntitlementModal);

export default EntitlementModalContainer;