import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import { createEntitlement, reissueEntitlement } from '../../data/actions/entitlement';
import { closeModal } from '../../data/actions/modal';

import EntitlementModal from './Modal';

const mapStateToProps = (state) => {
  return {
    isOpen: state.modal.isOpen,
    entitlement: state.modal.activeEntitlement,
  }
}

const mapDispatchToProps = dispatch => ({
  createEntitlement: ({username, courseUuid, mode, comments}) => dispatch(
    createEntitlement({username, courseUuid, mode, comments})
  ),
  reissueEntitlement: ({entitlement, comments}) => dispatch(
    reissueEntitlement({entitlement, comments})
  ),
  closeModal: () => dispatch(closeModal()),
});

const EntitlementModalContainer = connect(
  mapStateToProps,
  mapDispatchToProps
)(EntitlementModal);

export default EntitlementModalContainer;