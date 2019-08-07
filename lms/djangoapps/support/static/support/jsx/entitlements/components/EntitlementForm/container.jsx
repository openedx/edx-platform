import { connect } from 'react-redux';

import { createEntitlement, reissueEntitlement } from '../../data/actions/entitlement';
import { closeForm } from '../../data/actions/form';

import EntitlementForm from './index.jsx';

const mapStateToProps = state => ({
  formType: state.form.formType,
  isOpen: state.form.isOpen,
  entitlement: state.form.activeEntitlement,
});

const mapDispatchToProps = dispatch => ({
  createEntitlement: ({ username, courseUuid, mode, comments }) =>
    dispatch(createEntitlement({ username, courseUuid, mode, comments })),
  reissueEntitlement: ({ entitlement, comments }) =>
    dispatch(reissueEntitlement({ entitlement, comments })),
  closeForm: () => dispatch(closeForm()),
});

const EntitlementFormContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(EntitlementForm);

export default EntitlementFormContainer;
